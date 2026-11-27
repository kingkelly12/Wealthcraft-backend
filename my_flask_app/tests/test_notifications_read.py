"""The unread badge: reading clears exactly what it counts."""


def test_read_all_clears_the_badge(client, auth_headers, user_id, fake_supabase):
    fake_supabase.rows('profiles').append({'id': 'profile-1', 'user_id': user_id, 'username': 'me'})
    fake_supabase.rows('notifications').extend([
        {'id': 'n1', 'user_id': user_id, 'read': False}, {'id': 'n2', 'user_id': 'profile-1', 'read': False},
        {'id': 'n3', 'user_id': 'someone-else', 'read': False},
    ])
    unread = lambda: client.get('/api/notifications/unread/', headers=auth_headers).get_json()['data']
    assert unread() == 2
    assert client.put('/api/notifications/read-all/', headers=auth_headers).status_code == 200
    assert unread() == 0
    assert next(n for n in fake_supabase.rows('notifications') if n['id'] == 'n3')['read'] is False
