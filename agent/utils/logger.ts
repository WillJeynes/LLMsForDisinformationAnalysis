import winston from "winston";

export const logger = winston.createLogger({
  level: "info",
  format: winston.format.combine(
    winston.format.splat(),
    winston.format.colorize(),
    winston.format.timestamp({ format: "HH:mm:ss" }),
    winston.format.printf(({ level, message, timestamp }) => {
      return `${timestamp} ${level}: ${message}`;
    })
  ),
  transports: [
    new winston.transports.Console(),
  ],
});