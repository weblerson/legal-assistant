from ragflow_sdk import Chunk, RAGFlow


async def instantiate_rag_object(api_key: str, base_url: str) -> RAGFlow:
    rag_object = RAGFlow(api_key=api_key, base_url=base_url)

    return rag_object


async def retrieve_chunks(
        dataset_name: str,
        question: str,
        rag_object: RAGFlow,
) -> list[Chunk]:
    page_size = 10

    datasets = rag_object.list_datasets(name=dataset_name)
    dataset = datasets[0]

    documents = dataset.list_documents(page_size=page_size)
    document_ids = [d.id for d in documents]

    chunks = rag_object.retrieve(
        dataset_ids=[dataset.id],
        document_ids=document_ids,
        question=question,
    )

    return chunks
