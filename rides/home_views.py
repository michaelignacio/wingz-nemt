from django.shortcuts import render
from django.http import HttpResponse


def home(request):
    """Simple home page with API navigation links."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Wingz NEMT API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            h1 { color: #2c3e50; }
            .api-section { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
            .api-links a { display: block; margin: 5px 0; padding: 8px; background: #3498db; color: white; text-decoration: none; border-radius: 3px; }
            .api-links a:hover { background: #2980b9; }
            .auth-info { background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; }
            .credentials { background: #e8f5e8; padding: 10px; border-radius: 3px; margin: 5px 0; }
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
                <p><a href="/api-auth/login/" style="background: #28a745; color: white; padding: 8px 16px; text-decoration: none; border-radius: 3px;">Login to Browse API</a></p>
            </div>

            <div class="api-section">
                <h3>📚 API Endpoints</h3>
                <div class="api-links">
                    <a href="/api/api/">🏠 API Root - Start Here</a>
                    <a href="/api/api/users/">👥 Users Management</a>
                    <a href="/api/api/users/stats/">📊 User Statistics</a>
                    <a href="/api/api/rides/">🚗 Rides Management</a>
                    <a href="/api/api/rides/stats/">📈 Ride Statistics</a>
                    <a href="/api/api/ride-events/">📝 Ride Events</a>
                    <a href="/api/api/ride-events/stats/">📋 Event Statistics</a>
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

            <div class="api-section">
                <h3>🔧 Features</h3>
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
