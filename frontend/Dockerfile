# This complete, verified toolchain is also used for production static builds.
FROM cgr.dev/chainguard/wolfi-base@sha256:24f549a7fcace88e69b9557941168c74645688ecc4acf7fb6d734a6b74e9019d AS toolchain
RUN apk add --no-cache nodejs-24=24.22.2-r2 \
    && addgroup -g 1000 node \
    && adduser -D -u 1000 -G node -h /home/node node
RUN node --input-type=module -e 'import {createHash} from "node:crypto"; import {writeFileSync} from "node:fs"; const response = await fetch("https://registry.npmjs.org/npm/-/npm-11.21.2.tgz", {redirect: "error", signal: AbortSignal.timeout(60000)}); if (!response.ok) throw new Error("npm download failed"); const chunks = []; let total = 0; for await (const chunk of response.body) { total += chunk.length; if (total > 10 * 1024 * 1024) throw new Error("npm archive too large"); chunks.push(Buffer.from(chunk)); } const archive = Buffer.concat(chunks, total); if (createHash("sha512").update(archive).digest("base64") !== "7HPApk+AflMUavSseL1Pm6CnYqMIHk53x+KmuhqmTDqPkjPMgxIpTPcTqsE91EKNw4gFBJV9fnXiSdGm1DXq9A==") throw new Error("npm integrity mismatch"); writeFileSync("/tmp/npm.tgz", archive);' \
    && mkdir -p /usr/local/lib/node_modules/npm \
    && tar -xzf /tmp/npm.tgz --strip-components=1 -C /usr/local/lib/node_modules/npm \
    && rm /tmp/npm.tgz \
    && ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/bin/npm \
    && ln -s /usr/local/lib/node_modules/npm/bin/npx-cli.js /usr/bin/npx \
    && test "$(npm --version)" = 11.21.2

FROM toolchain AS dev

WORKDIR /app
RUN chown node:node /app
USER node

COPY --chown=node:node package.json package-lock.json ./
RUN npm ci

COPY --chown=node:node . .

EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173", "--strictPort"]
