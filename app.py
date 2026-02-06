import streamlit as st
import seaborn as sns
import pandas as pd
from matplotlib import pyplot as plt
import anthropic





st.set_page_config(
    page_title="LLM Data Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
#Chamando a api 
client=anthropic.Anthropic(api_key=st.secrets['ANTROPIC_API_KEY'])

def build_data_summary(df: pd.DataFrame) -> dict:
    """Return lightweight metadata used to build the prompt when the dataset is large."""
    sample_rows = df.head(min(len(df), 5)).to_string(index=False)
    try:
        stats_repr = df.describe(include="all").to_string()
    except Exception:
        stats_repr = "Statistics unavailable"
    return {
        "shape": df.shape,
        "columns": df.columns.tolist(),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "sample": sample_rows,
        "stats": stats_repr,
    }


#estado de inicialização da sessão
if "messages" not in st.session_state:
    st.session_state.messages=[]
if "df" not in st.session_state:
    st.session_state.df=None
if "data_summary" not in st.session_state:
    st.session_state.data_summary=None



st.title("LLM Data Analysis Application")

st.markdown("Upload your dataset and let the LLM assist you in analyzing it!")

with st.sidebar:
    st.header("Upload your Data")
    uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx"])

    if uploaded_file:
        try:

            df=pd.read_csv(uploaded_file)
            st.session_state.df=df
            st.session_state.data_summary = build_data_summary(df)
            st.success("File loaded successfully!")


            with st.expander("Preview Data"):
                st.dataframe(df.head())

            with st.expander("Dataset Info"):
                col1,col2=st.columns(2)

                with col1:
                    st.metric("Rows",df.shape[0])
                    st.metric("Columns",df.shape[1])
                with col2:
                    st.metric("Memory usage: ",f"{df.memory_usage().sum()/1024}")
                    st.metric("Missing values: ",f"{df.isnull().sum().sum()}")



        except Exception as e:
            st.warning("Error loading file")
    else:
        st.info("Upload you csv")


#Chat interface
if st.session_state.df is not None:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            # re-display figure
            if 'figure' in msg:
                st.pyplot(msg['figure'])
    user_input=st.chat_input("Ask any question about your data")

    if user_input:
        #add message to the variable messages
        st.session_state.messages.append({"role":"user","content":user_input})
    
        #Display the message
        with st.chat_message("user"):
            st.markdown(user_input)

        #Preparing the context
        df=st.session_state.df

        if len(df)>100:
            if not st.session_state.data_summary:
                st.session_state.data_summary = build_data_summary(df)
            data_context=f"""
            Dataset Shape:{st.session_state.data_summary['shape']}
            Columns: {', '.join(st.session_state.data_summary['columns'])}
            Data Types:{st.session_state.data_summary['dtypes']}
            Sample Rows:{st.session_state.data_summary['sample']}
            Basic statistics:{st.session_state.data_summary['stats']}
            """
        else:
            data_context=f"""
            Full_dataset:
            {df.to_string()}
            """

        #system prompt
        system_prompt=f""" You are a helpful data analyst assistant.
        The user has uploaded a CSV file with the following information:{data_context}

        the data is loaded in a pandas dataframe called 'df'

        Guidelines:
        1.ANSWER THE QUESTION CLEARLY
        2.IF THE QUESTION REQUIRES ANALYSIS WRITE PYTHON,MATPLOTLIB OR SEABORN 

        3.FOR VISUALIZATIONS ALWAQYS USE PLT.FIGURE, BEFORE PLOTING AND INCLUDE PLT.TIGHTLAYOUT 
        ALWAYS VALIDATE DATA BEFORE ANSWERS
        IF YOU CAN'T ANSWER, EXPLAIN WHY
        FOCUS ON DATA INSIGHTS ROUGHLY TO THE QUESTION ASKED


        WHEN WRITIN CODE:
            - IMPORT STATEMENT ARE ALREADY DONE
        """
        with st.chat_message("assistant"):
            with st.spinner("Thinking ... "):
                    try:

                        response = client.messages.create(
                            model="claude-3-5-haiku-latest",
                            max_tokens=1024,
                            system=system_prompt,
                            messages=[{"role":"user","content":user_input}],
                            temperature=0.1
                        )
                        reply="".join(
                            block.text for block in response.content if block.type == "text"
                        )

                        st.markdown(reply)

                        if "```python" in reply:
                            code_blocks=reply.split("```python")
                            for i in range(1,len(code_blocks)):
                                code=code_blocks[i].split("```")[0]
                        try:
                            plt.figure(figsize=(10,6))

                            exec_globals={
                                'df':df,
                                'pd':pd,
                                'plt':plt,
                                'sns':sns,
                                'st':st
                            }
                            exec(code.strip(),exec_globals)

                            fig =plt.gcf()
                            if fig.get_axes():
                                st.pyplot(fig)

                                #Save this figure
                                st.session_state.messages.append({
                                    'role':'assistant',
                                    'content':reply,
                                    'figure':fig
                                })

                            else:
                                st.session_state.messages.append({
                                    'role':'assistant',
                                    'content':reply
                                })

                                plt.close()

                        except Exception as e:
                            st.error(f"erro {e}")
                            st.code(code, language="python")



                        st.session_state.messages.append({"role":"Assitant","content":reply})



                    except Exception as e:
                        st.error(f"erro generating response:   {e}")
                        st.info("Please try again")






else:
    col1,col2,col3= st.columns([1,2,1])
    with col2:
        st.info("Please Upload a CSV file to start")

        st.markdown("Examples:")
        st.markdown("1- What are the main trend:")





    

#footer 

st.markdown ("--"*89)
st.markdown("""
            <div style='text-align: center;color:gray;font-size:12px;'>
            Tip: Be specific with your questions for better results |
            Your data stay private and is not stored
            </div>
            """, unsafe_allow_html=True)