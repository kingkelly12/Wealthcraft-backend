#!/usr/bin/env python3
from app import create_app, db
from sqlalchemy import inspect

def inspect_loans():
    app = create_app()
    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print("Tables available:", tables)
        
        target_tables = ['liabilities', 'bank_loans', 'p2p_loans']
        for table in target_tables:
            if table in tables:
                print(f"\n✅ Table '{table}' exists. Columns:")
                for col in inspector.get_columns(table):
                    print(f"  - {col['name']} ({col['type']})")
            else:
                print(f"\n❌ Table '{table}' does NOT exist.")

if __name__ == "__main__":
    inspect_loans()
