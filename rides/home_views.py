from django.shortcuts import render
from django.http import HttpResponse


def home(request):
    """Simple home page with API navigation links. Hides login button if user is authenticated."""
    is_authenticated = request.user.is_authenticated if hasattr(request, 'user') else False
    login_button = ""
    if not is_authenticated:
        login_button = '<p><a href="/api-auth/login/" style="background: #28a745; color: white; padding: 8px 16px; text-decoration: none; border-radius: 3px;">Login to Browse API</a></p>'
    # API endpoints and their labels
    api_links = [
        ("/api/", "🏠 API Root - Start Here"),
        ("/api/users/", "👥 Users Management"),
        ("/api/users/stats/", "📊 User Statistics"),
        ("/api/rides/", "🚗 Rides Management"),
        ("/api/rides/stats/", "📈 Ride Statistics"),
        ("/api/ride-events/", "📝 Ride Events"),
        ("/api/ride-events/stats/", "📋 Event Statistics"),
        ("/api/rides/?gps_latitude=37.7749&amp;gps_longitude=-122.4194", "✨ GPS-Based Sorting Example"),
        ("/api/rides/nearby/?gps_latitude=37.7749&amp;gps_longitude=-122.4194&amp;radius=5", "✨ Nearby Rides Example"),
        ("/api/ride-events/todays_events/", "✨ Today's Events Example"),
        ("/api/users/?role=driver&amp;is_active=true", "✨ Filter Users by Role"),
        ("/api/rides/?status=active&amp;start_date=2025-01-01", "✨ Filter Rides by Status and Date"),
        ("/api/users/?search=john", "✨ Search Users by Name or Email"),
        ("/api/ride-events/?event_type=pickup&amp;ride_id=123", "✨ Filter Events by Type and Ride"),
    ]

    # Render links as <a> if authenticated, <span> if not
    api_links_html = ""
    if is_authenticated:
        for url, label in api_links:
            api_links_html += f'<a href="{url}">{label}</a>'
    else:
        for url, label in api_links:
            api_links_html += f'<span class="disabled-link">{label}</span>'

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Wingz NEMT API</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .container {{ max-width: 800px; margin: 0 auto; }}
            h1 {{ color: #2c3e50; }}
            .api-section {{ margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
            .api-links a {{ display: block; margin: 5px 0; padding: 8px; background: #3498db; color: white; text-decoration: none; border-radius: 3px; }}
            .api-links a:hover {{ background: #2980b9; }}
            .api-links .disabled-link {{ display: block; margin: 5px 0; padding: 8px; background: #ccc; color: #888; border-radius: 3px; cursor: not-allowed; text-decoration: none; }}
            .auth-info {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; }}
            .credentials {{ background: #e8f5e8; padding: 10px; border-radius: 3px; margin: 5px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚗 Wingz NEMT API</h1>
            <p>Welcome to the Wingz Non-Emergency Medical Transportation API!</p>
            
            <div class="auth-info">
                <h3>🔐 Authentication Required</h3>
                <p>All API endpoints require admin authentication. Use these credentials:</p>
                <div class="credentials">
                    <strong>Email:</strong> admin@wingz.com<br>
                    <strong>Password:</strong> admin123
                </div>
                {login_button}
            </div>

            <div class="api-section">
                <h3>📚 API Endpoints</h3>
                <div class="api-links">
                    {api_links_html}
                </div>
            </div>

            <div class="api-section">
                <h3>🧪 Test Accounts</h3>
                <p>Available test accounts for different roles:</p>
                <ul>
                    <li><strong>Admin:</strong> admin@wingz.com / admin123</li>
                    <li><strong>Driver:</strong> driver@wingz.com / driver123</li>
                    <li><strong>Rider:</strong> rider@wingz.com / rider123</li>
                    <li><strong>Dispatcher:</strong> dispatcher@wingz.com / dispatcher123</li>
                </ul>
            </div>

            <div class="api-section" id="special-features">
                <h3>🔧 Special Features</h3>
                <ul>
                    <li>✅ Complete User Management</li>
                    <li>✅ Ride Tracking & GPS Sorting</li>
                    <li>✅ Real-time Event Logging</li>
                    <li>✅ Statistics & Analytics</li>
                    <li>✅ Token-based Authentication</li>
                    <li>✅ Browsable API Interface</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html)
