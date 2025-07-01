-- scripts/setup_script.sql
-- This script supports browsing multiple stages via direct grants.

-- Step 1: Create Application Roles
CREATE OR REPLACE APPLICATION ROLE app_admin;
CREATE OR REPLACE APPLICATION ROLE app_viewer;

-- Step 2: Create Schemas for UI and Core Logic
CREATE OR REPLACE SCHEMA app_ui;
GRANT USAGE ON SCHEMA app_ui TO APPLICATION ROLE app_admin;
GRANT USAGE ON SCHEMA app_ui TO APPLICATION ROLE app_viewer;

CREATE OR REPLACE SCHEMA app_core;
GRANT USAGE ON SCHEMA app_core TO APPLICATION ROLE app_admin;
GRANT USAGE ON SCHEMA app_core TO APPLICATION ROLE app_viewer;

-- Step 3: Create a table to store the names of registered stages
CREATE OR REPLACE TABLE app_core.registered_stages (
    stage_name VARCHAR
);
GRANT SELECT ON TABLE app_core.registered_stages TO APPLICATION ROLE app_admin;
GRANT SELECT ON TABLE app_core.registered_stages TO APPLICATION ROLE app_viewer;
GRANT INSERT, DELETE ON TABLE app_core.registered_stages TO APPLICATION ROLE app_admin;

-- Step 4: Create a procedure to add a stage to the list
CREATE OR REPLACE PROCEDURE app_core.add_stage(name_of_stage STRING)
RETURNS STRING
LANGUAGE SQL
AS
$$
BEGIN
    INSERT INTO app_core.registered_stages (stage_name) VALUES (:name_of_stage);
    RETURN 'SUCCESS: Stage ' || :name_of_stage || ' was registered.';
END;
$$;
GRANT USAGE ON PROCEDURE app_core.add_stage(STRING) TO APPLICATION ROLE app_admin;

-- Step 5: Create a procedure to remove a stage from the list
CREATE OR REPLACE PROCEDURE app_core.remove_stage(name_of_stage STRING)
RETURNS STRING
LANGUAGE SQL
AS
$$
BEGIN
    DELETE FROM app_core.registered_stages WHERE stage_name = :name_of_stage;
    RETURN 'SUCCESS: Stage ' || :name_of_stage || ' was unregistered.';
END;
$$;
GRANT USAGE ON PROCEDURE app_core.remove_stage(STRING) TO APPLICATION ROLE app_admin;

-- Step 5: Create a dummy procedure for the admin check
CREATE OR REPLACE PROCEDURE app_core.is_admin_check()
RETURNS BOOLEAN
LANGUAGE SQL
AS
$$
BEGIN
    RETURN TRUE;
END;
$$;
-- IMPORTANT: Grant USAGE only to app_admin. app_viewer will get a permission error.
GRANT USAGE ON PROCEDURE app_core.is_admin_check() TO APPLICATION ROLE app_admin;


-- Step 6: Create the Streamlit UI Object
CREATE OR REPLACE STREAMLIT app_ui.main
  FROM '/app'
  MAIN_FILE = '/streamlit_app.py';

-- Grant usage on the Streamlit app to both roles.
GRANT USAGE ON STREAMLIT app_ui.main TO APPLICATION ROLE app_admin;
GRANT USAGE ON STREAMLIT app_ui.main TO APPLICATION ROLE app_viewer;


-- Step 7: Create a warehouse for the application to use
CREATE WAREHOUSE IF NOT EXISTS STAGE_BROWSER_WH3
  WAREHOUSE_SIZE = 'X-SMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE;

-- Grant the application role usage on the new warehouse
GRANT USAGE ON WAREHOUSE STAGE_BROWSER_WH3 TO APPLICATION ROLE app_admin;
GRANT USAGE ON WAREHOUSE STAGE_BROWSER_WH3 TO APPLICATION ROLE app_viewer;
