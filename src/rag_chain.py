from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain_classic.chains import ConversationalRetrievalChain

from .prompt import PROMPT_TEMPLATE
from .vectorstore import create_hybrid_retriever
from .llm import load_llm


def create_rag_chain():
    retriever = create_hybrid_retriever()
    llm = load_llm()

    # System prompt for instructions
    system = SystemMessagePromptTemplate.from_template(PROMPT_TEMPLATE)
    human = HumanMessagePromptTemplate.from_template("Lịch sử chat:\n{chat_history}\n\nBối cảnh (Context):\n{context}\n\nCâu hỏi mới:\n{question}")
    
    prompt = ChatPromptTemplate.from_messages([system, human])

    # Using ConversationalRetrievalChain for memory support
    qa = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        combine_docs_chain_kwargs={"prompt": prompt},
        return_source_documents=True,
    )

    return qa
