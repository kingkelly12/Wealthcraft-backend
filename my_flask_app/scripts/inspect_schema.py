#!/usr/bin/env python3
"""
Inspect actual Supabase database schema to identify all columns
"""
from app import create_app, db
from sqlalchemy import inspect

def inspect_database_schema():
    """Inspect the actual database schema"""
    app = create_app()
    
    with app.app_context():
        print("=" * 70)
        print("SUPABASE DATABASE SCHEMA INSPECTION")
        print("=" * 70)
        
        try:
            inspector = inspect(db.engine)
            
            # Get profiles table columns
            print("\n📊 PROFILES TABLE COLUMNS:")
            print("-" * 70)
            profiles_columns = inspector.get_columns('profiles')
            for col in profiles_columns:
                col_type = str(col['type'])
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                default = f" DEFAULT {col['default']}" if col.get('default') else ""
                print(f"  {col['name']:<30} {col_type:<20} {nullable}{default}")
            
            print(f"\n  Total columns: {len(profiles_columns)}")
            
            # List all column names for easy copying
            print("\n  Column names (for model definition):")
            column_names = [col['name'] for col in profiles_columns]
            for name in column_names:
                print(f"    - {name}")
            
        except Exception as e:
            print(f"❌ Error inspecting schema: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    inspect_database_schema()
