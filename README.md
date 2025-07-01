# Snowflake Multi-Stage Browser

This Snowflake Native Application allows you to securely register and browse files from multiple internal or external stages directly from a unified Streamlit interface.

## How It Works

This application uses a direct-grant security model. Instead of using the UI to grant access, **you (the consumer)** run standard `GRANT` commands in a worksheet to give the application explicit, read-only access to specific stages you want it to browse.

This model provides:
- **Flexibility:** Register and browse as many different stages as you need.
- **Clear Permissions:** The permissions are managed through standard SQL, making them easy to audit and control.
- **Security:** The application only has the permissions you explicitly grant it.

---

## **IMPORTANT: Post-Installation Setup**

After installing this application, you **MUST** run the following SQL commands for **EACH STAGE** you want the application to access. The app will not be able to see or list files from any stage until you do.

Run these commands in a Snowflake worksheet. Replace `{db_name}`, `{sch_name}`, and `{stg_name}` with the actual names of your objects.

```sql
-- Replace these placeholders with your actual object names.
SET (db_name, sch_name, stg_name) = ('YOUR_DATABASE', 'YOUR_SCHEMA', 'YOUR_STAGE');

-- Grant the application USAGE on the database and schema containing the stage.
GRANT USAGE ON DATABASE IDENTIFIER($db_name) TO APPLICATION AWS_S3_BROWSER_APP;
GRANT USAGE ON SCHEMA IDENTIFIER($sch_name) TO APPLICATION AWS_S3_BROWSER_APP;

-- Grant the application READ on the stage itself.
GRANT READ ON STAGE IDENTIFIER($stg_name) TO APPLICATION AWS_S3_BROWSER_APP;
```

---

## Application Usage

1.  **Grant Permissions:** Run the SQL commands listed above for at least one stage.
2.  **Open the App:** Navigate to the installed application in Snowsight.
3.  **Register a Stage:** In the "Manage Stages" section of the app, enter the fully qualified name of the stage you just granted access to (e.g., `YOUR_DATABASE.YOUR_SCHEMA.YOUR_STAGE`) and click "Add Stage".
4.  **Browse Files:**
    - Select the desired stage from the dropdown menu at the top.
    - Click "Refresh File List" to view its contents.

You can add or remove stages from the application at any time using the management interface.
