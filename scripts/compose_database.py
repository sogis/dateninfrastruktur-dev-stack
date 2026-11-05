"""Bounded PostgreSQL diagnostics on the explicitly selected Compose project."""

def target_sql(context, db, query):
    args = ['exec','-T','postgres','psql','-X','-q','-At','-U','postgres','-d',db,'-v','ON_ERROR_STOP=1']
    return context.command(args, input=query).stdout.strip()

def row_hash_sql(query):
    return "SELECT encode(sha256(convert_to(coalesce(string_agg(to_jsonb(row_data)::text,E'\\n' ORDER BY to_jsonb(row_data)::text COLLATE \"C\"),''),'UTF8')),'hex') FROM ("+query.rstrip(';')+") row_data"
