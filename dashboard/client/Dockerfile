FROM node:14-alpine
WORKDIR /app

# Install app dependencies
COPY package.json yarn.lock ./
RUN yarn

# Build app
COPY . ./
RUN yarn build

ENTRYPOINT ["yarn", "start"]