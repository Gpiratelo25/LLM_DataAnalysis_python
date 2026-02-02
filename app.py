import streamlit as st
import pandas as pd
import anthropic


st.set_page_config(
    page_title="LLM Data Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
#Chamando a api 
client=anthropic.Anthropic(api_key=st.secrets['ANTROPIC_API_KEY'])


#estado de inicialização da sessão
if "messages" not in st.session_state:
    st.session_state.messages=[]
if "df" not in st.session_state:
    st.session_state.df=None
if "data_summary" not in st.session_state:
    st.session_state.data_summary=None



st.title("📊 LLM Data Analysis Application")

st.markdown("Upload your dataset and let the LLM assist you in analyzing it!")

with st.sidebar:
    st.header("Upload your Data")
    uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx"])

    if uploaded_file:
        try:

            df=pd.read_csv(uploaded_file)
            st.session_state.df=df
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

        Guidelines:
        1.ANWSER THE QUESTION CLEARLY
        2.FOCUSING ON PROVIDING DATA INSIGHTS
        3.BE SPECIFIC AND HELPFUL
        """
        with st.chat_message("assistant"):
            with st.spinner("Thinking ... "):
                    try:

                        response = client.messages.create(
                            model="claude-3-5-sonnet-20241022",
                            max_tokens=1024,
                            messages=[
                                {"role":"system","content":system_prompt},
                                {"role":"user","content":user_input}
                            ],
                            temperature=0.1
                        )
                        reply= response.content

                        st.markdown(reply)

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


    

