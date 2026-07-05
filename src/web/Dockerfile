FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm install

COPY . .

EXPOSE 5177

CMD ["npx", "vite", "--host", "0.0.0.0", "--port", "5177"]
