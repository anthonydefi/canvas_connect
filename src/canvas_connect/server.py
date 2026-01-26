"""Canvas Connect MCP Server - Main server implementation."""

import os
import logging
from typing import Any
from datetime import datetime

from mcp.server import Server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)
from canvasapi import Canvas
from canvasapi.course import Course
from canvasapi.exceptions import CanvasException

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("canvas-connect")

# Initialize MCP server
app = Server("canvas-connect")

# Global Canvas instance
canvas_instance: Canvas | None = None
course_instance: Course | None = None


def get_canvas() -> Canvas:
    """Get or create Canvas API instance."""
    global canvas_instance
    if canvas_instance is None:
        api_url = os.getenv("CANVAS_API_URL")
        api_token = os.getenv("CANVAS_API_TOKEN")

        if not api_url or not api_token:
            raise ValueError(
                "Missing Canvas API credentials. Please set CANVAS_API_URL and CANVAS_API_TOKEN environment variables."
            )

        canvas_instance = Canvas(api_url, api_token)
        logger.info(f"Connected to Canvas at {api_url}")

    return canvas_instance


def get_course() -> Course:
    """Get or create Course instance."""
    global course_instance
    if course_instance is None:
        canvas = get_canvas()
        course_id = os.getenv("CANVAS_COURSE_ID")

        if not course_id:
            raise ValueError(
                "Missing course ID. Please set CANVAS_COURSE_ID environment variable."
            )

        course_instance = canvas.get_course(int(course_id))
        logger.info(f"Loaded course: {course_instance.name}")

    return course_instance


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available Canvas management tools."""
    return [
        # Assignment tools
        Tool(
            name="list_assignments",
            description="List all assignments in the course with their details (name, due date, points, published status)",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="create_assignment",
            description="Create a new assignment in the course",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Assignment name"},
                    "description": {"type": "string", "description": "Assignment description (HTML supported)"},
                    "points": {"type": "number", "description": "Points possible"},
                    "due_at": {"type": "string", "description": "Due date in ISO format (e.g., 2024-12-31T23:59:59)"},
                    "published": {"type": "boolean", "description": "Whether to publish immediately", "default": False},
                },
                "required": ["name", "points"],
            },
        ),
        Tool(
            name="get_assignment_submissions",
            description="Get all submissions for a specific assignment",
            inputSchema={
                "type": "object",
                "properties": {
                    "assignment_id": {"type": "number", "description": "Assignment ID"},
                },
                "required": ["assignment_id"],
            },
        ),
        Tool(
            name="update_grade",
            description="Update a student's grade for an assignment",
            inputSchema={
                "type": "object",
                "properties": {
                    "assignment_id": {"type": "number", "description": "Assignment ID"},
                    "user_id": {"type": "number", "description": "Student user ID"},
                    "grade": {"type": "string", "description": "Grade (number or letter)"},
                    "comment": {"type": "string", "description": "Optional comment"},
                },
                "required": ["assignment_id", "user_id", "grade"],
            },
        ),

        # Student tools
        Tool(
            name="list_students",
            description="List all students enrolled in the course",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_student_grades",
            description="Get a student's grades across all assignments",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "number", "description": "Student user ID"},
                },
                "required": ["user_id"],
            },
        ),
        Tool(
            name="get_grade_summary",
            description="Get a summary of all students with their current total grade/score in the course",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),

        # Announcement tools
        Tool(
            name="list_announcements",
            description="List recent announcements in the course",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "number", "description": "Number of announcements to retrieve", "default": 10},
                },
            },
        ),
        Tool(
            name="create_announcement",
            description="Create a new announcement in the course",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Announcement title"},
                    "message": {"type": "string", "description": "Announcement message (HTML supported)"},
                    "published": {"type": "boolean", "description": "Whether to publish immediately", "default": True},
                },
                "required": ["title", "message"],
            },
        ),

        # Module tools
        Tool(
            name="list_modules",
            description="List all modules in the course",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_module_items",
            description="Get all items in a specific module",
            inputSchema={
                "type": "object",
                "properties": {
                    "module_id": {"type": "number", "description": "Module ID"},
                },
                "required": ["module_id"],
            },
        ),
        Tool(
            name="create_module",
            description="Create a new module in the course",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Module name"},
                    "published": {"type": "boolean", "description": "Whether to publish immediately", "default": False},
                },
                "required": ["name"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls for Canvas operations."""
    try:
        course = get_course()

        # Assignment tools
        if name == "list_assignments":
            assignments = course.get_assignments()
            result = []
            for assignment in assignments:
                result.append(
                    f"ID: {assignment.id}\n"
                    f"Name: {assignment.name}\n"
                    f"Points: {getattr(assignment, 'points_possible', 'N/A')}\n"
                    f"Due: {getattr(assignment, 'due_at', 'No due date')}\n"
                    f"Published: {getattr(assignment, 'published', False)}\n"
                )
            return [TextContent(type="text", text="\n---\n".join(result) if result else "No assignments found")]

        elif name == "create_assignment":
            assignment_data = {
                "name": arguments["name"],
                "points_possible": arguments["points"],
                "published": arguments.get("published", False),
            }
            if "description" in arguments:
                assignment_data["description"] = arguments["description"]
            if "due_at" in arguments:
                assignment_data["due_at"] = arguments["due_at"]

            assignment = course.create_assignment({"assignment": assignment_data})
            return [TextContent(
                type="text",
                text=f"Assignment created successfully!\nID: {assignment.id}\nName: {assignment.name}\nPoints: {assignment.points_possible}"
            )]

        elif name == "get_assignment_submissions":
            assignment = course.get_assignment(arguments["assignment_id"])
            submissions = assignment.get_submissions()
            result = []
            for submission in submissions:
                user = course.get_user(submission.user_id)
                result.append(
                    f"Student: {user.name} (ID: {user.id})\n"
                    f"Score: {getattr(submission, 'score', 'Not graded')}\n"
                    f"Submitted: {getattr(submission, 'submitted_at', 'Not submitted')}\n"
                    f"Status: {getattr(submission, 'workflow_state', 'Unknown')}"
                )
            return [TextContent(type="text", text="\n---\n".join(result) if result else "No submissions found")]

        elif name == "update_grade":
            assignment = course.get_assignment(arguments["assignment_id"])
            submission = assignment.get_submission(arguments["user_id"])

            update_data = {"posted_grade": arguments["grade"]}
            if "comment" in arguments:
                update_data["comment"] = {"text_comment": arguments["comment"]}

            submission.edit(submission=update_data)
            return [TextContent(
                type="text",
                text=f"Grade updated successfully for user {arguments['user_id']}: {arguments['grade']}"
            )]

        # Student tools
        elif name == "list_students":
            students = course.get_users(enrollment_type=["student"])
            result = []
            for student in students:
                result.append(
                    f"ID: {student.id}\n"
                    f"Name: {student.name}\n"
                    f"Email: {getattr(student, 'email', 'N/A')}\n"
                    f"SIS ID: {getattr(student, 'sis_user_id', 'N/A')}"
                )
            return [TextContent(type="text", text="\n---\n".join(result) if result else "No students found")]

        elif name == "get_student_grades":
            user_id = arguments["user_id"]
            user = course.get_user(user_id)
            
            # Get enrollment with grades
            enrollments = course.get_enrollments(user_id=[user_id], include=['current_points', 'current_score'])
            enrollment = None
            for enroll in enrollments:
                if enroll.user_id == user_id and enroll.type == 'StudentEnrollment':
                    enrollment = enroll
                    break
            
            result = [f"Student: {user.name}"]
            
            # Add overall grade if available
            if enrollment:
                current_score = getattr(enrollment, 'grades', {}).get('current_score', 'N/A')
                final_score = getattr(enrollment, 'grades', {}).get('final_score', 'N/A')
                result.append(f"Current Score: {current_score}%")
                result.append(f"Final Score: {final_score}%")
                result.append("")
            
            # Get individual assignment grades
            assignments = course.get_assignments()
            result.append("Assignment Grades:")
            for assignment in assignments:
                try:
                    submission = assignment.get_submission(user_id)
                    score = getattr(submission, 'score', None)
                    points_possible = getattr(assignment, 'points_possible', 0)
                    if score is not None:
                        result.append(f"  {assignment.name}: {score}/{points_possible}")
                    else:
                        result.append(f"  {assignment.name}: Not graded")
                except Exception:
                    result.append(f"  {assignment.name}: No submission")

            return [TextContent(type="text", text="\n".join(result))]

        elif name == "get_grade_summary":
            students = course.get_users(enrollment_type=["student"])
            student_list = list(students)

            if not student_list:
                return [TextContent(type="text", text="No students found in the course")]

            # Get enrollments with grades for all students
            user_ids = [s.id for s in student_list]
            enrollments = course.get_enrollments(
                type=["StudentEnrollment"],
                include=["current_points", "total_scores"]
            )

            # Build a map of user_id to enrollment grades
            enrollment_map = {}
            for enrollment in enrollments:
                if enrollment.type == "StudentEnrollment":
                    enrollment_map[enrollment.user_id] = enrollment

            result = ["=" * 60]
            result.append("STUDENT GRADE SUMMARY")
            result.append("=" * 60)
            result.append("")

            # Sort students by name
            student_list.sort(key=lambda s: s.name)

            for student in student_list:
                enrollment = enrollment_map.get(student.id)

                if enrollment and hasattr(enrollment, 'grades'):
                    grades = enrollment.grades
                    current_score = grades.get('current_score', 'N/A')
                    current_grade = grades.get('current_grade', '')
                    final_score = grades.get('final_score', 'N/A')
                    final_grade = grades.get('final_grade', '')

                    # Format the score display
                    score_display = f"{current_score}%" if current_score != 'N/A' else "N/A"
                    if current_grade:
                        score_display += f" ({current_grade})"

                    final_display = f"{final_score}%" if final_score != 'N/A' else "N/A"
                    if final_grade:
                        final_display += f" ({final_grade})"

                    result.append(f"Student: {student.name}")
                    result.append(f"  ID: {student.id}")
                    result.append(f"  Current Score: {score_display}")
                    result.append(f"  Final Score: {final_display}")
                else:
                    result.append(f"Student: {student.name}")
                    result.append(f"  ID: {student.id}")
                    result.append(f"  Current Score: No grades available")

                result.append("")

            result.append("=" * 60)
            result.append(f"Total Students: {len(student_list)}")
            result.append("=" * 60)

            return [TextContent(type="text", text="\n".join(result))]

        # Announcement tools
        elif name == "list_announcements":
            limit = arguments.get("limit", 10)
            announcements = course.get_discussion_topics(only_announcements=True)
            result = []
            count = 0
            for announcement in announcements:
                if count >= limit:
                    break
                result.append(
                    f"ID: {announcement.id}\n"
                    f"Title: {announcement.title}\n"
                    f"Posted: {getattr(announcement, 'posted_at', 'N/A')}\n"
                    f"Message: {getattr(announcement, 'message', 'N/A')[:200]}..."
                )
                count += 1
            return [TextContent(type="text", text="\n---\n".join(result) if result else "No announcements found")]

        elif name == "create_announcement":
            announcement = course.create_discussion_topic(
                title=arguments["title"],
                message=arguments["message"],
                is_announcement=True,
                published=arguments.get("published", True),
            )
            return [TextContent(
                type="text",
                text=f"Announcement created successfully!\nID: {announcement.id}\nTitle: {announcement.title}"
            )]

        # Module tools
        elif name == "list_modules":
            modules = course.get_modules()
            result = []
            for module in modules:
                result.append(
                    f"ID: {module.id}\n"
                    f"Name: {module.name}\n"
                    f"Published: {getattr(module, 'published', False)}\n"
                    f"Items: {getattr(module, 'items_count', 0)}"
                )
            return [TextContent(type="text", text="\n---\n".join(result) if result else "No modules found")]

        elif name == "get_module_items":
            module = course.get_module(arguments["module_id"])
            items = module.get_module_items()
            result = [f"Module: {module.name}\n"]
            for item in items:
                result.append(
                    f"  - {item.title} ({item.type})"
                )
            return [TextContent(type="text", text="\n".join(result))]

        elif name == "create_module":
            module = course.create_module(
                module={"name": arguments["name"], "published": arguments.get("published", False)}
            )
            return [TextContent(
                type="text",
                text=f"Module created successfully!\nID: {module.id}\nName: {module.name}"
            )]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except CanvasException as e:
        logger.error(f"Canvas API error: {e}")
        return [TextContent(type="text", text=f"Canvas API error: {str(e)}")]
    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the MCP server."""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
