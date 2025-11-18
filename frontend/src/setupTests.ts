import '@testing-library/jest-dom';
import { server } from './mocks/server';

// MSW: APIモックの起動/停止
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

