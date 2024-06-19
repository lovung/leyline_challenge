# Use an official Node.js runtime as a parent image
FROM node:18-alpine

# Set the working directory in the container
WORKDIR /app

# Copy the package.json and package-lock.json files
COPY package*.json ./

# Install the dependencies
RUN npm install

# Copy the rest of the application code into the container
COPY . .

# Build the Next.js application
# RUN npm run build

# Expose port 3000
EXPOSE 3000

# Command to run the Next.js application
CMD ["npm", "run", "dev"]

