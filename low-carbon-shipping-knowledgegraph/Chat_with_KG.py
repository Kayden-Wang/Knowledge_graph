import logging
import os
from timeit import default_timer as timer

import dotenv
import streamlit as st
from langchain.chains import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from streamlit_chat import message

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
dotenv.load_dotenv()

# Define constants for environment variables
OPENAI_API_BASE_URL = "OPENAI_API_BASE_URL"
OPENAI_API_KEY = "OPENAI_API_KEY"
NEO4J_CONNECTION_URL = "NEO4J_CONNECTION_URL"
NEO4J_USER = "NEO4J_USER"
NEO4J_PASSWORD = "NEO4J_PASSWORD"

# Get environment variables with validation
def get_env_var(var_name: str) -> str:
    """Retrieves an environment variable with error handling."""
    var_value = os.getenv(var_name)
    if not var_value:
        raise ValueError(f"Environment variable {var_name} not found.")
    return var_value

try:
    openai_api_base_url = get_env_var(OPENAI_API_BASE_URL)
    openai_api_key = get_env_var(OPENAI_API_KEY)
    neo4j_url = get_env_var(NEO4J_CONNECTION_URL)
    neo4j_user = get_env_var(NEO4J_USER)
    neo4j_password = get_env_var(NEO4J_PASSWORD)
except ValueError as e:
    logger.error(f"Error loading environment variables: {e}")
    st.error("Error loading environment variables. Please check configuration.")
    st.stop()

# OpenAI API configuration
llm = ChatOpenAI(
    openai_api_base=openai_api_base_url,
    openai_api_key=openai_api_key,
    model_name="moonshot-v1-32k",
)

# Cypher generation prompt
cypher_generation_template = """
你是一位 Neo4j Cypher翻译专家，根据提供的Neo4j schema 将中文查询转换为Cypher，按照以下指示进行操作：

1. 生成仅与Neo4j版本5兼容的Cypher查询
2. 不使用 EXISTS、SIZE、HAVING 关键字。使用WITH关键字时使用别名
3. 仅使用 schema 中提到的节点和关系
4. 对任何属性相关的搜索，始终进行不区分大小写和模糊搜索。例如：搜索散货船时，使用 `toLower(ShipType.name) contains 'bulk carrier'`。搜索名为"IMO DCS"的法规时，使用 `toLower(Regulation.name) contains 'imo dcs'`。
5. 永远不要使用 schema 中未提到的关系
6. 当被问及与数值相关的比较时，例如大于、小于，请确保将属性值转换为浮点数进行比较。例如，要查找d1值大于0.8的油船，使用`toFloat(ShipType.d1) > 0.8 AND toLower(ShipType.name) contains 'tanker'`
7. 你的回答生成的Cypher不应该含有中文字符.

schema : {schema}

注意:
由于KG数据库不含有中文, 首先将中文查询中的实体或关系名称匹配到 schema 中 的英文名称至关重要。
例如，
* “散货船” 映射到 "Bulk carrier"
* “AER指标” 映射到 "Annual Efficiency Ratio (AER)"
* “参考运力类型”映射到"refCapacityType"。

示例：
问题：我要查询油轮的CII评级界限线计算公式
回答：```MATCH (s:ShipType {{name: "Tanker"}}), (b:Boundary) RETURN s.name AS ship_type, b.name AS boundary, b.formula```
问题：集装箱船可适用的修正系数及其计算方法是什么
回答：```MATCH (s:ShipType {{name: "Container ship"}})-[:applicableCorrectionFactor]->(cf:CorrectionFactor) RETURN s.name AS ship_type, cf.name AS correction_factor, cf.formula AS formula, cf.remarks AS remarks```
问题：请给我温控集装箱船舶的CII计算需采用的修正系数
回答：```MATCH (s:Ship)-[:hasShipType]->(st:ShipType), (st)-[:applicableCorrectionFactor]->(cf:CorrectionFactor {{name: "Refrigerated container CF"}}) RETURN s.name AS ship, cf.name AS correction_factor, cf.formula```

question : {question}
"""

cypher_prompt = PromptTemplate(
    template=cypher_generation_template,
    input_variables=["schema", "question"]
)

# Cypher QA prompt
CYPHER_QA_TEMPLATE = """
你是一位助手，帮助形成清晰且易于理解的答案。
信息部分包含了你必须使用来构建答案的提供信息。
提供的信息是权威的，你绝不能怀疑它或试图使用你内部的知识来纠正它。
让答案听起来像是对问题的回应。不要提到你是基于给定的信息得出的结果。
如果提供的信息为空，请说你不知道答案。
最终答案应易于阅读和结构清晰。

Information:
{context}

Question: {question}

有帮助的回答：

"""
qa_prompt = PromptTemplate(
    input_variables=["context", "question"], template=CYPHER_QA_TEMPLATE
)

def query_graph(user_input: str) -> dict:
    """Queries the Neo4j graph database with the user's input."""
    try:
        graph = Neo4jGraph(url=neo4j_url, username=neo4j_user, password=neo4j_password)

        # 测试数据库连接
        try:
            graph.query("MATCH (n) RETURN count(n)")
            logger.info("数据库连接成功！")
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            # 抛出异常，以便调用函数可以处理它
            raise

        # # 打印 schema 信息 (可选)
        # schema = graph.get_structured_schema
        # logger.info("Schema:")
        # logger.info(schema)

        chain = GraphCypherQAChain.from_llm(
            llm=llm,
            graph=graph,
            verbose=True,
            return_intermediate_steps=True,
            cypher_prompt=cypher_prompt,
            qa_prompt=qa_prompt
        )
        result = chain.invoke(user_input)
        return result
    except Exception as e:
        logger.error(f"Error querying graph database: {e}")
        raise

# Streamlit app
st.set_page_config(layout="wide")

# Initialize user and system messages
if "user_msgs" not in st.session_state:
    st.session_state.user_msgs = []
if "system_msgs" not in st.session_state:
    st.session_state.system_msgs = []

# Layout the application
title_col, empty_col, img_col = st.columns([2, 1, 2])

# Display title and image
with title_col:
    st.title("航运低碳 Neo4j 助手")
with img_col:
    st.image("https://dist.neo4j.com/wp-content/uploads/20210423062553/neo4j-social-share-21.png", width=200)

# User input area
user_input = st.text_input("输入你的问题: ", key="input")

# Process user input
if user_input:
    with st.spinner("Processing your question..."):
        st.session_state.user_msgs.append(user_input)
        start = timer()
        try:
            result = query_graph(user_input)

            # Extract intermediate steps and results
            intermediate_steps = result.get("intermediate_steps", [])
            cypher_query = intermediate_steps[0]["query"] if intermediate_steps else ""
            database_results = intermediate_steps[1]["context"] if len(intermediate_steps) > 1 else ""

            # Display the answer
            answer = result["result"]
            st.session_state.system_msgs.append(answer)

        except Exception as e:
            st.error("An error occurred while processing your request.")
            logger.error(f"Error processing user input: {e}")
            cypher_query = ""
            database_results = ""

    st.write(f"Time taken: {timer() - start:.2f}s")

    # Layout results and technical details
    col1, col2, col3 = st.columns([1, 1, 1])

    # Display the chat history
    with col1:
        if st.session_state["system_msgs"]:
            for i in range(len(st.session_state["system_msgs"]) - 1, -1, -1):
                message(st.session_state["system_msgs"][i], key=str(i) + "_assistant")
                message(st.session_state["user_msgs"][i], is_user=True, key=str(i) + "_user")

    # Display the last Cypher query
    with col2:
        if cypher_query:
            st.text_area("Last Cypher Query", cypher_query, key="_cypher", height=240)

    # Display the last database results
    with col3:
        if database_results:
            st.text_area("Last Database Results", database_results, key="_database", height=240)