# Stage 1: Build the frontend
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files and install ALL dependencies (including dev)
COPY package*.json ./
RUN npm install

# Copy the rest of the application code
COPY . .

# Build the production frontend assets
RUN npm run build

# Stage 2: Final runtime image
FROM node:20-alpine

WORKDIR /app

# Copy only the necessary files from the builder stage
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/server.ts ./
COPY --from=builder /app/node_modules ./node_modules

# Set the environment to production
ENV NODE_ENV=production

# The app defaults to port 3000
EXPOSE 3000

# Start the server using the production script
CMD ["npm", "start"]
