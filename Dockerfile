# Dockerfile
FROM node:lts-alpine

# Set the working directory
WORKDIR /usr/src/app

# Copy package files first to leverage Docker's caching
COPY package*.json ./

# Install dependencies
RUN npm install
RUN npm install -g nodemon

# Copy the rest of your application code
COPY . .

# Expose the port your app runs on
EXPOSE 3000

# Command to run your app
CMD ["node", "app.js", "nodemon"]
