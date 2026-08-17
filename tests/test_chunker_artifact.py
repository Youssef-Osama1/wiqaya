import json

from src.core.chunking.chunker import write_chunks_jsonl
from src.core.schemas import Chunk


class TestWriteChunksJsonl:
    def test_writes_one_json_line_per_chunk(self, tmp_path):
        out_path = write_chunks_jsonl("nice_ng136", tmp_path)
        lines = out_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) > 0

    def test_each_line_round_trips_as_chunk(self, tmp_path):
        out_path = write_chunks_jsonl("nice_ng136", tmp_path)
        first_line = out_path.read_text(encoding="utf-8").strip().split("\n")[0]
        chunk = Chunk.model_validate(json.loads(first_line))
        assert chunk.metadata.doc_key == "nice_ng136"

    def test_output_filename_matches_doc_key_convention(self, tmp_path):
        out_path = write_chunks_jsonl("who_hypertension", tmp_path)
        assert out_path.name == "who_hypertension_chunks.jsonl"
