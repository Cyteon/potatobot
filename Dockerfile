# Use an official Node.js runtime as a parent image
FROM node:18-bookworm-slim

# Set the working directory in the container to /app
WORKDIR /app

# Add the current directory contents into the container at /app
ADD . /app

# Install any needed packages
RUN npm install

# Make port 443 available to the world outside this container
EXPOSE 443

# Run PotatoBot when the container launches
CMD ["node", "."]
