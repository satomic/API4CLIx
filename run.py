#!/usr/bin/env python3
"""
启动脚本 for API4CLIx
"""

import os
import sys
import argparse

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import uvicorn


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="API4CLIx - API Layer for AI Programming Assistants")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--log-level", default="info", choices=["debug", "info", "warning", "error"],
                       help="Log level (default: info)")

    args = parser.parse_args()

    print(f"""
🚀 Starting API4CLIx...

API Documentation will be available at:
  • Swagger UI: http://{args.host}:{args.port}/docs
  • ReDoc: http://{args.host}:{args.port}/redoc
  • Health Check: http://{args.host}:{args.port}/health

Supported AI Assistants:
  • GitHub Copilot CLI (gh copilot)
  • More coming soon...

Press Ctrl+C to stop the server.
""")

    try:
        uvicorn.run(
            "main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level=args.log_level
        )
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down API4CLIx. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()