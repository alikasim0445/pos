# Point-of-Sale Management System

This project is a Point-of-Sale (POS) Management System designed to support multiple warehouses. It consists of a frontend built with React and a backend that can be implemented using either FastAPI or Django REST Framework. The database used for this project is PostgreSQL.

## Project Structure

The project is organized into the following main directories:

- **frontend**: Contains the React application for the POS system.
  - **src**: The source code for the React application, including components, pages, services, hooks, and contexts.
  - **public**: Contains the static files, including the main HTML file.
  - **package.json**: Configuration file for npm, listing dependencies and scripts.
  - **tsconfig.json**: TypeScript configuration file.

- **backend**: Contains the backend implementation.
  - **fastapi**: FastAPI implementation of the backend.
  - **django**: Django implementation of the backend.
  - Each backend implementation has its own README.md for specific documentation.

- **infra**: Contains infrastructure-related files, including Docker configurations.
- **sql**: Contains SQL scripts for initializing the database.
- **.env.example**: Example environment variable configuration for the project.

## Features

- Multi-warehouse support for managing inventory across different locations.
- User authentication and authorization.
- CRUD operations for products and warehouses.
- Sales processing interface for handling transactions.

## Getting Started

To get started with the project, follow these steps:

1. Clone the repository:
   ```
   git clone <repository-url>
   cd pos-management-system
   ```

2. Set up the backend:
   - Navigate to either the `fastapi` or `django` directory and follow the instructions in the respective README.md file to set up the backend.

3. Set up the frontend:
   - Navigate to the `frontend` directory and install the dependencies:
     ```
     npm install
     ```
   - Start the development server:
     ```
     npm start
     ```

4. Configure the database:
   - Modify the `.env` file with your database credentials and run the SQL scripts in the `sql` directory to initialize the database.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or features you would like to add.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.