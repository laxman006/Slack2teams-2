"""
Semantic chunking strategy for document processing.

Implements heading-aware chunking with fallback to sliding window approach.
Optimized for retrieval quality and context preservation.
"""

import re
from typing import List, Tuple
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import tiktoken

# Token estimation: ~5.5 chars per token on average for English
CHARS_PER_TOKEN = 5.5

# Configuration (can be overridden by config.py)
DEFAULT_TARGET_TOKENS = 800
DEFAULT_OVERLAP_TOKENS = 200
DEFAULT_MIN_TOKENS = 150


class SemanticChunker:
    """
    Semantic chunking with heading awareness and sliding window fallback.
    """
    
    def __init__(
        self,
        target_tokens: int = DEFAULT_TARGET_TOKENS,
        overlap_tokens: int = DEFAULT_OVERLAP_TOKENS,
        min_tokens: int = DEFAULT_MIN_TOKENS,
        model: str = "cl100k_base"  # OpenAI default encoding
    ):
        """
        Initialize semantic chunker.
        
        Args:
            target_tokens: Target chunk size in tokens (~800)
            overlap_tokens: Overlap between chunks in tokens (~200)
            min_tokens: Minimum chunk size - merge smaller chunks (~150)
            model: Tokenizer model name
        """
        self.target_tokens = target_tokens
        self.overlap_tokens = overlap_tokens
        self.min_tokens = min_tokens
        
        # Convert tokens to approximate characters
        self.chunk_size = int(target_tokens * CHARS_PER_TOKEN)
        self.chunk_overlap = int(overlap_tokens * CHARS_PER_TOKEN)
        self.min_chunk_size = int(min_tokens * CHARS_PER_TOKEN)
        
        # Initialize tokenizer for accurate token counting
        try:
            self.encoding = tiktoken.get_encoding(model)
        except:
            # Fallback if tiktoken fails
            self.encoding = None
        
        # Heading patterns (Markdown and HTML)
        self.heading_patterns = [
            r'^#{1,6}\s+.+$',  # Markdown: # Heading, ## Heading, etc.
            r'^<h[1-6]>.*?</h[1-6]>$',  # HTML: <h1>Heading</h1>
            r'^[A-Z][A-Za-z\s]{2,50}:$',  # Title case with colon (e.g., "Section Title:")
        ]
        
        # Initialize fallback splitter
        self.fallback_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=[
                "\n\n\n",  # Multiple blank lines
                "\n\n",    # Paragraph breaks
                "\n",      # Line breaks
                ". ",      # Sentence breaks
                "! ",      # Exclamation
                "? ",      # Question
                "; ",      # Semicolon
                ", ",      # Comma
                " ",       # Word breaks
                ""         # Character breaks
            ]
        )
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if self.encoding:
            return len(self.encoding.encode(text))
        else:
            # Fallback: estimate based on characters
            return int(len(text) / CHARS_PER_TOKEN)
    
    def is_heading(self, line: str) -> bool:
        """Check if a line is likely a heading."""
        line = line.strip()
        if not line:
            return False
        
        for pattern in self.heading_patterns:
            if re.match(pattern, line, re.MULTILINE):
                return True
        
        return False
    
    def split_by_headings(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Split text by headings, returning chunks with character positions.
        
        Returns:
            List of (chunk_text, start_pos, end_pos)
        """
        lines = text.split('\n')
        chunks = []
        current_chunk = []
        current_start = 0
        char_position = 0
        
        for i, line in enumerate(lines):
            line_with_newline = line + '\n' if i < len(lines) - 1 else line
            line_length = len(line_with_newline)
            
            # Check if this is a heading and we have content in current chunk
            if self.is_heading(line) and current_chunk and i > 0:
                # Save current chunk
                chunk_text = ''.join(current_chunk).strip()
                if chunk_text:
                    chunks.append((chunk_text, current_start, char_position))
                
                # Start new chunk with this heading
                current_chunk = [line_with_newline]
                current_start = char_position
            else:
                current_chunk.append(line_with_newline)
            
            char_position += line_length
        
        # Add final chunk
        if current_chunk:
            chunk_text = ''.join(current_chunk).strip()
            if chunk_text:
                chunks.append((chunk_text, current_start, char_position))
        
        return chunks
    
    def merge_small_chunks(self, chunks: List[Tuple[str, int, int]]) -> List[Tuple[str, int, int]]:
        """Merge chunks smaller than min_tokens with adjacent chunks."""
        if not chunks:
            return chunks
        
        merged = []
        i = 0
        
        while i < len(chunks):
            chunk_text, start_pos, end_pos = chunks[i]
            token_count = self.count_tokens(chunk_text)
            
            # If chunk is too small, try to merge with next chunk
            if token_count < self.min_tokens and i < len(chunks) - 1:
                next_text, next_start, next_end = chunks[i + 1]
                combined_text = chunk_text + "\n\n" + next_text
                combined_tokens = self.count_tokens(combined_text)
                
                # If combined is still reasonable, merge
                if combined_tokens < self.target_tokens * 1.5:
                    merged.append((combined_text, start_pos, next_end))
                    i += 2  # Skip next chunk since we merged it
                    continue
            
            # Keep chunk as is
            merged.append((chunk_text, start_pos, end_pos))
            i += 1
        
        return merged
    
    def split_large_chunks(self, chunks: List[Tuple[str, int, int]]) -> List[Tuple[str, int, int]]:
        """Split chunks larger than target_tokens using sliding window."""
        result = []
        
        for chunk_text, start_pos, end_pos in chunks:
            token_count = self.count_tokens(chunk_text)
            
            # If chunk is within acceptable range, keep it
            if token_count <= self.target_tokens * 1.3:
                result.append((chunk_text, start_pos, end_pos))
            else:
                # Split using fallback splitter
                sub_docs = self.fallback_splitter.create_documents([chunk_text])
                current_pos = start_pos
                
                for sub_doc in sub_docs:
                    sub_text = sub_doc.page_content
                    sub_length = len(sub_text)
                    result.append((sub_text, current_pos, current_pos + sub_length))
                    current_pos += sub_length - self.chunk_overlap
        
        return result
    
    def chunk_text(self, text: str) -> List[Tuple[str, int, int, int]]:
        """
        Chunk text semantically with heading awareness.
        
        Returns:
            List of (chunk_text, start_pos, end_pos, token_count)
        """
        if not text or not text.strip():
            return []
        
        # Step 1: Try to split by headings
        chunks = self.split_by_headings(text)
        
        # Step 2: Merge small chunks
        chunks = self.merge_small_chunks(chunks)
        
        # Step 3: Split large chunks
        chunks = self.split_large_chunks(chunks)
        
        # Step 4: Add token counts
        result = []
        for chunk_text, start_pos, end_pos in chunks:
            token_count = self.count_tokens(chunk_text)
            result.append((chunk_text, start_pos, end_pos, token_count))
        
        return result
    
    def chunk_document(self, document: Document) -> List[Document]:
        """
        Chunk a LangChain Document with semantic awareness.
        
        Args:
            document: Input document with content and metadata
        
        Returns:
            List of chunked documents with preserved metadata
        """
        text = document.page_content
        chunks = self.chunk_text(text)
        
        if not chunks:
            return []
        
        chunked_docs = []
        for i, (chunk_text, start_pos, end_pos, token_count) in enumerate(chunks):
            # Create new document with chunk
            chunk_doc = Document(
                page_content=chunk_text,
                metadata={
                    **document.metadata,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "char_range": f"{start_pos}-{end_pos}",
                    "token_count": token_count
                }
            )
            chunked_docs.append(chunk_doc)
        
        return chunked_docs
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """
        Chunk multiple documents.
        
        Args:
            documents: List of documents to chunk
        
        Returns:
            List of chunked documents
        """
        all_chunks = []
        for doc in documents:
            chunks = self.chunk_document(doc)
            all_chunks.extend(chunks)
        
        return all_chunks


def chunk_documents_semantically(
    documents: List[Document],
    target_tokens: int = DEFAULT_TARGET_TOKENS,
    overlap_tokens: int = DEFAULT_OVERLAP_TOKENS,
    min_tokens: int = DEFAULT_MIN_TOKENS
) -> List[Document]:
    """
    Convenience function to chunk documents semantically.
    
    Args:
        documents: Documents to chunk
        target_tokens: Target chunk size in tokens
        overlap_tokens: Overlap in tokens
        min_tokens: Minimum chunk size in tokens
    
    Returns:
        List of chunked documents
    """
    chunker = SemanticChunker(
        target_tokens=target_tokens,
        overlap_tokens=overlap_tokens,
        min_tokens=min_tokens
    )
    
    return chunker.chunk_documents(documents)

