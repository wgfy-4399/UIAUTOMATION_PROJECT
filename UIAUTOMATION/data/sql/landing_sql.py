query_chapters_by_id_sql = """
    SELECT * FROM fq_chapters WHERE id=%s
"""