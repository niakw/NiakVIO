FROM node:20-alpine

WORKDIR /app

COPY package.json ./
RUN npm install --omit=dev --ignore-scripts

COPY server.js channels.json blacklist.config.json ./

ENV NODE_ENV=production
ENV HOST=0.0.0.0
ENV PORT=7000

EXPOSE 7000

CMD ["npm", "start"]
