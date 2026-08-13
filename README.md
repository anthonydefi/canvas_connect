# Canvas Connect MCP Server

A Model Context Protocol (MCP) server for managing Canvas LMS courses. This server enables you to manage assignments, students, announcements, and course modules through the Canvas API.

## Features

### Assignment Management
- List all assignments with details (due dates, points, publish status)
- Create new assignments with descriptions and due dates
- View assignment submissions
- Update student grades and add comments

### Student Management
- List all enrolled students
- View individual student grades across all assignments
- Track student progress

### Announcements
- List recent course announcements
- Create new announcements with rich text

### Module & Content Management
- List all course modules
- View module contents and items
- Create new modules

### Discussion & Grading Tools
- View discussion posts and replies with word counts
- Get grading rubrics for assignments
- AI writing detection to check for AI-generated student submissions

## Setup

### 1. Install Dependencies

First, create a virtual environment and install the package:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

### 2. Get Canvas API Credentials

1. Log into your Canvas LMS instance
2. Go to Account → Settings
3. Scroll down to "Approved Integrations"
4. Click "+ New Access Token"
5. Give it a purpose (e.g., "MCP Server") and click "Generate Token"
6. Copy the token immediately (you won't be able to see it again)

### 3. Find Your Course ID

Your course ID is in the URL when viewing your course:
```
https://your-institution.instructure.com/courses/[COURSE_ID]
```

### 4. Configure Environment Variables

Copy the example environment file and fill in your details:

```bash
cp .env.example .env
```

Edit `.env` with your information:

```bash
CANVAS_API_URL=https://your-institution.instructure.com
CANVAS_API_TOKEN=your_api_token_here
CANVAS_COURSE_ID=your_course_id_here
CANVAS_COURSE_NAME=Section 1  # Optional label, shown by list_courses
ANTHROPIC_API_KEY=your_anthropic_api_key_here  # Required for AI detection feature

# Optional: teaching a second course (e.g. another section)?
# CANVAS_COURSE_ID_2=your_second_course_id_here
# CANVAS_COURSE_NAME_2=Section 2
```

If you set `CANVAS_COURSE_ID_2`, every tool accepts an optional `course_id` argument
(raw course ID, slot number `1`/`2`, or the label you set) to target that course instead
of the default. Run `list_courses` to see what's configured.

### 5. Get Anthropic API Key (Optional - for AI Detection)

The AI writing detection feature requires an Anthropic API key:

1. Go to [console.anthropic.com](https://console.anthropic.com/)
2. Create an account or log in
3. Navigate to API Keys
4. Create a new API key
5. Add credits to your account (Plans & Billing)
6. Add the key to your `.env` file as `ANTHROPIC_API_KEY`

**Note**: The AI detection feature uses Claude to analyze student posts. Each analysis costs a small amount of API credits.

### 6. Configure Claude Desktop

Add the server to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "canvas-connect": {
      "command": "/Users/anthony/Documents/code/canvas_connect/venv/bin/python",
      "args": ["-m", "canvas_connect.server"],
      "env": {
        "CANVAS_API_URL": "https://your-institution.instructure.com",
        "CANVAS_API_TOKEN": "your_api_token_here",
        "CANVAS_COURSE_ID": "your_course_id_here",
        "CANVAS_COURSE_ID_2": "your_second_course_id_here"
      }
    }
  }
}
```

**Important**: Update the paths and credentials with your actual values.

### 7. Restart Claude Desktop

After saving the configuration, restart Claude Desktop to load the MCP server.

## Available Tools

Every tool below also accepts an optional **course_id** argument for selecting between
multiple configured courses (see "Configure Environment Variables" above). Omit it to use
the default course.

### Course Tools

#### `list_courses`
List the Canvas courses configured for this server, with their IDs and names.

### Assignment Tools

#### `list_assignments`
List all assignments in the course with their details.

#### `create_assignment`
Create a new assignment.
- **name** (required): Assignment name
- **points** (required): Points possible
- **description**: Assignment description (HTML supported)
- **due_at**: Due date in ISO format (e.g., "2024-12-31T23:59:59")
- **published**: Whether to publish immediately (default: false)

#### `get_assignment_submissions`
Get all submissions for a specific assignment.
- **assignment_id** (required): Assignment ID

#### `update_grade`
Update a student's grade for an assignment.
- **assignment_id** (required): Assignment ID
- **user_id** (required): Student user ID
- **grade** (required): Grade (number or letter)
- **comment**: Optional comment

### Student Tools

#### `list_students`
List all students enrolled in the course.

#### `get_student_grades`
Get a student's grades across all assignments.
- **user_id** (required): Student user ID

### Announcement Tools

#### `list_announcements`
List recent announcements in the course.
- **limit**: Number of announcements to retrieve (default: 10)

#### `create_announcement`
Create a new announcement.
- **title** (required): Announcement title
- **message** (required): Announcement message (HTML supported)
- **published**: Whether to publish immediately (default: true)

### Module Tools

#### `list_modules`
List all modules in the course.

#### `get_module_items`
Get all items in a specific module.
- **module_id** (required): Module ID

#### `create_module`
Create a new module.
- **name** (required): Module name
- **published**: Whether to publish immediately (default: false)

### Discussion Tools

#### `get_discussion_posts`
Get all posts and replies for a discussion topic with word counts.
- **topic_id** (required): Discussion topic ID
- **user_id**: Optional filter for a specific student's posts

#### `get_rubric`
Get the grading rubric for a specific assignment.
- **assignment_id** (required): Assignment ID

### AI Detection Tools

#### `check_ai_writing`
Analyze a student's discussion post to detect if it was likely written by AI such as ChatGPT or Claude.
- **topic_id** (required): Discussion topic ID
- **user_id** (required): Student user ID to check

Returns:
- Likelihood assessment (Low/Medium/High)
- Confidence level
- Key indicators found in the text
- Summary of the analysis

**Note**: This feature requires an Anthropic API key. See setup instructions above.

## Example Usage

Once configured, you can ask Claude to help manage your course:

- "List all assignments in my course"
- "Create a new assignment called 'Lab 3: Python Basics' worth 50 points, due next Friday"
- "Show me all submissions for assignment 12345"
- "Update the grade for student 67890 on assignment 12345 to 85 with a comment 'Great work!'"
- "List all students in my course"
- "Show me the grades for student 67890"
- "Create an announcement titled 'Office Hours Change' with the message 'Office hours moved to Tuesday 2-4pm'"
- "List all modules"
- "Show me what's in module 5"
- "Create a new module called 'Week 3: Control Structures'"
- "Show me all the discussion posts for the Introductions discussion"
- "Get the rubric for assignment 1027200"
- "Check if student 127920 used AI to write their discussion post"

## Security Notes

- Your Canvas API token has the same permissions as your Canvas account
- Keep your `.env` file secure and never commit it to version control
- The token is stored in Claude Desktop's configuration - ensure your computer is secure
- Consider creating a dedicated Canvas account with limited permissions for the MCP server

## Troubleshooting

### Server not showing up in Claude Desktop
- Check that the path to Python in the config is correct (use `which python` while your venv is activated)
- Verify your environment variables are set correctly
- Check Claude Desktop logs for errors

### Canvas API errors
- Verify your API token is valid
- Check that your course ID is correct
- Ensure your Canvas account has sufficient permissions
- Some institutions may restrict API access

### Connection issues
- Verify the Canvas API URL is correct (should end with `.instructure.com`)
- Check your internet connection
- Ensure Canvas is not undergoing maintenance

## Development

To run the server directly for testing:

```bash
python -m canvas_connect.server
```

## License

MIT License - feel free to modify and use for your courses.

## Contributing

This is a personal project for managing Canvas LMS courses. Feel free to fork and adapt for your needs.
