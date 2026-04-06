import pkg from 'pg';
const { Pool } = pkg;

/**
 * Postgres pool fixture for integration assertions.
 *
 * Usage in a test file:
 *   const rows = await db.query('SELECT status FROM workflows WHERE id=$1', [id]);
 *   expect(rows[0].status).toBe('active');
 *
 * Connection string is read from DATABASE_URL env var.
 * Tests only SELECT — never INSERT/UPDATE/DELETE except cleanup in afterEach.
 */
export function makeDbFixture() {
  const pool = new Pool({
    connectionString: process.env.DATABASE_URL || 'postgresql://acos:acos_dev_password@localhost:5432/acos',
    max: 2,
    idleTimeoutMillis: 10000,
  });

  const db = {
    /**
     * Run a SQL query and return all rows.
     * @param {string} sql
     * @param {any[]} [params]
     * @returns {Promise<Record<string, any>[]>}
     */
    async query(sql, params = []) {
      const result = await pool.query(sql, params);
      return result.rows;
    },

    async end() {
      await pool.end();
    },
  };

  return db;
}
