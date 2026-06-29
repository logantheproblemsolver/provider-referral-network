/**
 * This file is for the authentication middleware to make sure that this service can't be accessed without authentication
 */
import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';

const SERVICE_JWT_SECRET = process.env.SERVICE_JWT_SECRET;

// This will make sure that if there is no service_jwt_secret the application will crash
if (!SERVICE_JWT_SECRET) {
  console.error('SERVICE_JWT_SECRET is required');
  process.exit(1);
}

/**
 * This validates the service JWT from resource-api, checking the signature, issuer, audience, and expiry
 */
export function requireServiceAuth(req: Request, res: Response, next: NextFunction): void {
  const authHeader = req.headers.authorization;
  if (!authHeader?.startsWith('Bearer ')) {
    res.status(401).json({ error: 'Missing authorization header' });
    return;
  }
  const token = authHeader.slice(7);
  try {
    jwt.verify(token, SERVICE_JWT_SECRET as string, {
      issuer: 'resource-api',
      audience: 'verification-svc',
      algorithms: ['HS256'],
    });
    next();
  } catch {
    res.status(401).json({ error: 'Invalid or expired service token' });
  }
}
