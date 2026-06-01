FROM node:20-slim

WORKDIR /app/frontend

COPY frontend/package.json frontend/yarn.lock ./
RUN npm install -g yarn && yarn install --frozen-lockfile

COPY frontend .

EXPOSE 19006
CMD ["yarn", "web", "--host", "0.0.0.0"]
