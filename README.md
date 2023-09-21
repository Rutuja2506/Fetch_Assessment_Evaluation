# AWS SQS to PostgreSQL Data Transformation

This application is designed to read user login behavior JSON data from an AWS SQS Queue, mask Personally Identifiable Information (PII), and store the masked data in a PostgreSQL database. The application is intended to run in a local development environment using Docker and LocalStack but can be adapted for production use.

## Table of Contents
- [Setup](#setup)
    - [Requirements](#requirements)
- [Project Structure](#project-structure)
- [Running the Application](#running-the-application)
- [Thought Process](#thought-process)
    - [Decisions and Assumptions](#decisions-and-assumptions)
- [Next Steps](#next-steps)
- [Questions](#questions)
    - [Production Ready](#productionready)
    - [Scalability](#scalability)
    - [Recovery of PII Data](#recovery-of-pii-data)
    - [Assumptions](#assumptions)
- [Conclusion](#conclusion)

## Setup
### Requirements

- Docker
- Python 3.x
- Python libraries : boto3, hashlib, psycopg2, os, load_dotenv
- PostgreSQL
- Docker Compose

### Installation Guidelines
- Python https://www.python.org/downloads/
- After installing Python, insatll python libraries by following command
    ```
    pip install boto3 
    pip install json 
    pip install hashlib 
    pip install psycopg2 
    pip install load_dotenv
    pip install awscli-local
    ```
- Docker -- docker install guide https://docs.docker.com/get-docker/
- PostgresSQL https://www.postgresql.org/download/
- Docker compose https://docs.docker.com/compose/install/

## Project Structure
The main components of this project:
- **application.py**: The Python script that connects to SQS, processes messages, masks PII data, and inserts records into Postgres.
- **docker-compose.yml**: Defines the Docker containers and configurations for LocalStack and Postgres.
- **README.md** : This README file with instructions on how to run the application.

## Running the Application
1. **Clone the Repository**: Clone this repository to your local machine.

2. **Run Docker Compose**: Open a terminal, navigate to the project directory, and run the following command to start the necessary containers:
    1. Use docker pull command to pull docker image for SQS queue and PostgresSQL
    2. Ensure you have docker-compose.yml file in the directory where you have cloned the project.
    3. Use following command for running up docker images.
        ```
        docker-compose up
        ```
       This will start LocalStack and PostgreSQL containers.

3. **Execute the Application**: Once the containers are up and running, execute the application script as follows:

   ```
   python application.py
   ```
   This script is data pipeline to fetch the data from Amazon SQS queue and insert it into PostgresSQl database.

## Thought Process 

In this section, we'll discuss the thought process behind the implementation of this application:

1. Reading Messages from the Queue: We use the boto3 library to interact with AWS SQS. We configure it to use the LocalStack endpoint for local development.

2. Data Structure: JSON data is received from the SQS Queue. We parse it into a Python list for processing.

3. Masking PII Data: To protect personal identifiable information (PII), we use a hashing function (SHA-256) to mask the device_id and ip fields. This ensures that duplicate values can still be identified, but the original data remains confidential.

    ```
    def mask_pii(data):
        """
        Masks personal identifiable information (PII) in the data.

        Args:
            data (str): The data to be masked.

        Returns:
            str: The masked data.
        """
        # Create a hash of the original data for easy duplicate identification
        hashed_data = hashlib.sha256(data.encode()).hexdigest()

        # Replace the original data with the hashed value
        return hashed_data
    ```   
4. Writing to PostgreSQL: Established a connection to a PostgreSQL database using the psycopg2 library. The application inserts the transformed data into the user_logins table with the required fields.
    ```
    import psycopg2

    def write_to_postgresql(data):
        """
        Establishes a connection to a PostgreSQL database and inserts transformed data into the 'user_logins' table.

        Args:
            data (tuple): A tuple containing data to be inserted into the 'user_logins' table.

        Returns:
            bool: True if the data was successfully inserted, False otherwise.
        """
        try:
            # Establish a connection to the PostgreSQL database
            connection = psycopg2.connect(
                user='your_username',
                password='your_password',
                host='your_database_host',
                port='your_database_port',
                database='your_database_name'
            )

            # Create a cursor object to interact with the database
            cursor = connection.cursor()

            # Define the SQL query to insert data into the 'user_logins' table
            insert_query = """
                INSERT INTO user_logins (user_id, device_type, masked_ip, masked_device_id, locale, app_version, create_date)
                VALUES (%s, %s, %s, %s, %s, %s, CURRENT_DATE);
            """

            # Execute the SQL query with the provided data
            cursor.execute(insert_query, data)

            # Commit the transaction to save the changes to the database
            connection.commit()

            # Close the cursor and the database connection
            cursor.close()
            connection.close()

            return True

        except (Exception, psycopg2.Error) as error:
            # Handle any exceptions that may occur during the database operation
            print("Error while writing to PostgreSQL:", error)
            return False
    ```

5. Closing Connections: After processing, the script closes the database connection to ensure proper resource management.

### Decisions and Assumptions
Here are the key decisions and assumptions made during the development of this application:

**Data Transformation and Masking**
- The application processes JSON data retrieved from an SQS Queue.
PII data, specifically device_id and ip, is masked using SHA-256 hashing with salting. Salting ensures that identical PII data entries result in different hash values, making it easy to identify duplicates.
- The code does not handle cases where 'app_version' cannot be converted to an integer. You may consider adding additional error handling for this scenario.

**Database Structure**
- The application stores data in a PostgreSQL database using the provided table schema for 'user_logins'.
- The 'app_version' column in the database table is altered to use the VARCHAR data type to accommodate non-integer values.

## Next Steps

If I had more time to work on this project, I would have considered implementing following enhancements and make it production-ready:

- **Testing**: Implement unit tests and integration tests to ensure the reliability of the application. Use testing frameworks such as pytest and unittest.
- **Scalability**: Consider using a message queue service like Kafka in a real AWS environment for better scalability. Implement load balancing and partitioning strategies.
- **Deployment**: For production deployment, consider containerization (e.g., Docker) and container orchestration (e.g., Kubernetes) to manage the application's lifecycle.
- Implement **logging** to record application events and errors.
- Set up **continuous integration and continuous deployment (CI/CD)** pipelines and would optimize database queries for improved performance with large datasets.

## Questions 

## Production Ready
**How would you deploy this application in production?**

To deploy this application in production, I would consider following steps:
- AWS Account: To set up production ready infrastructure and AWS is more popular choice due to its managed services including SQS and RDS (For Postgres)
- Docker Containers: Containerize the python application using Docker and by creating the docker image and pushing them to Amazon ECR or Docker Hub
- Container orchestration: Use orchestration tools like Kubernetes to manage and scale the application containers.

**What other components would you want to add to make this production ready?**

Other components I would like to add to make this production ready are as follows:
- **Environment Variables**: 
  - Storing sensitive configurations such as database credentials and AWS access keys as environment variables in your production environment.
- **Database configurations**:
  - **Amazon RDS** – for production ready Postgres database using Amazon RDS by ensuring database schema matching the DDL script.
- **Database security**: 
  - Implementing strong security measures using AWS KMS
- **Secret Manager**:
    - Using secret management services like AWS Manager for securely manage and rotate my application’s secret. Avoid hardcoding secrets in your application code.
- **Deployment strategy**: Continuous CI/ CD: For automating build, testing and deployment process of application.
- **Monitoring and Logging** – Amazon CloudWatch for monitoring application performance, resource utilization and error rates. Set up logging to store logs for easy analysis.
- **Documentation** – Maintain an up-to-date documentation which includes 	installation instructions, architecture diagrams, troubleshooting guides.
- **Version Control**- **Git** to track changes in application’s source codes, configuration files.

### Scalability
**How can this application scale with a growing dataset?**

Scaling this application with a growing dataset involves optimizing various components of the system to handle increased data volume and processing demands efficiently. Here are strategies for scaling this application:
- Vertical scaling – By upgrading Postgres databases resources (Suitable for moderate increase in data volume)
- Horizontal scaling – As dataset continues to grow, considering e horizontal scaling like PostgreSQL replication, sharding, or partitioning to distribute data, which ensure better handling of larger datasets and higher query loads.
- Distributed Data Processing: Considering frameworks like Apache Kafka or Apache Flink which allows parallel processing and scaling horizontally across multiple nodes making suitable for handling larger datasets and complex processing tasks.
- Caching : Using (Redis/ Memcached) to store frequently accessed data in memory  and reducing the load on the database along with improving response times, particularly for read-heavy operations.
- AWS Lambda : For serverless data processing and automatically scaling on demand.

### Recovery of PII Data

**How can PII be recovered later on?**

To recover PII data later on, you would need a secure process in place for authorized personnel to access the original data. This process might involve:

- **Data Retention Policies**: Define data retention policies to determine how long the masked data is kept in the database.

- **Data Archiving**: Archive the original data with proper encryption and access controls.

- **Access Control**: Implement strict access controls and authentication mechanisms to ensure only authorized personnel can access the PII recovery process.

### Assumptions
**What are the assumptions you made?**
- This application assumes that the LocalStack and Postgres containers are running locally with the provided configurations.
- It assumes that the SQS Queue contains JSON messages following a specific format.
- It masks PII data using **SHA-256** hashing, which can be reversed if needed for authorized purposes.
- Focuses on core data functions (read, mask, write); real-world apps need extra steps for integrity and security.
- The provided Postgres table schema matches the expected format of the processed data, with the exception of the *'app_version'* field. To accommodate non-integer data, the data type of the *'app_version'* field was changed from the originally mentioned integer to text/varchar. This change was necessary to prevent data from being stored as '0' or null when it couldn't be represented as an integer.

## Conclusion
This README provides an overview of the application, its structure, and instructions for running it. 




