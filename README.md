**Bulk Load PLSQL** 

Steps To execute the Project:

**Clone the repository:**
git clone https://github.com/Nirupa3112/Bulk_load_plsql.git
cd Bulk_load_plsql

**Install dependencies:**
pip install -r requirements.txt

**PostgreSQL Setup:**
brew services start postgresql@16
createdb bulk_load 
psql -d bulk_load
SELECT current_database();
\q

Configure env:
Create .env file (vi .env)
paste below details in .env file
DATABASE_URL=postgresql://YOUR_USERNAME@localhost:5432/bulk_load
check whoami and get username and change the username in above command in .env file

Create DB tables:

Run:
psql -d bulk_load -f app/database_schema.sql
 
psql -s bulk_load
\dt
We should be able to see 2 tables ingestion and constituents

exit: \q

Kickstart FastAPI:

Start Uvicorn:
uvicorn main:app --reload --port 8001

API dns:  http://127.0.0.1:8001/docs

Test the services:

Upload csv file in API and we should be able to see data in table
can verify by checking below command

open parallel terminal and check below
psql -d bulk_load
select count(*) from constituents;
select * from ingestions;

Test deletion of a row by giving id number
when deleted the deleted_at attribute in constituents table should have value instead of null
and it should not be physically delted from table

Test export, Can be exported as csv and json file

**Design Details:**

I have connected API to postgresSQL through psycopg,

**DataBase Design**

We have 2 main tables

**Ingestion** : To keep track of number of ingestions/uploads: Stores id, filename,loaded_at, row_count
**Constituents** : Table where csv id loaded to : id, ingestion_id ,index_code ,isin ,ticker ,name ,weight ,shares ,effective_date ,deleted_at

**Repository Design:**
main.py
Creates and configures the FastAPI application and registers the API routes.
app/config.py
Loads configuration from environment variables.
app/database.py
Creates and manages the PostgreSQL connection pool using Psycopg.
app/database_schema.sql
Contains the SQL required to create the PostgreSQL tables and indexes.
app/routes/
Contains the HTTP endpoints.
app/services/
Contains application/business logic such as CSV processing.
app/repositories/
Contains the SQL queries used to interact with PostgreSQL.
app/schemas.py
Contains Pydantic response models.
