#!/usr/bin/env python3
"""Test script to verify Flask app initialization and routes"""
from app import create_app

def test_flask_app():
    try:
        app = create_app('development')
        print('✓ Flask app created successfully')
        print('\nRegistered routes:')
        routes = []
        for rule in app.url_map.iter_rules():
            if rule.endpoint != 'static':
                methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
                routes.append(f'  {rule.rule:<50} [{methods}]')
        
        for route in sorted(routes):
            print(route)
        
        print(f'\n✓ Total routes: {len(routes)}')
        return True
    except Exception as e:
        print(f'✗ Error creating Flask app: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_flask_app()
    exit(0 if success else 1)
