/**
 * buy_wellknowns_data.js
 * Purchases the Well Knowns agent-index and MCP infrastructure datasets
 * via x402 micropayment. These are used to enrich x402 company entries
 * with live well-known endpoint signals.
 *
 * Usage: node scripts/buy_wellknowns_data.js
 *
 * Saves to:
 *   public/wellknowns-agent-index-{date}.json
 *   public/wellknowns-mcp-infra-{date}.json
 */
import { createWalletClient, http, toHex, getAddress } from 'viem';
import { privateKeyToAccount } from 'viem/accounts';
import { base } from 'viem/chains';
import { writeFileSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const BASE_URL = 'https://well-knowns.resolved.sh';

// ─── Wallet setup ─────────────────────────────────────────────────────────────
const account = privateKeyToAccount(`0x${process.env.WALLET_PRIVATE_KEY}`);
const walletClient = createWalletClient({ account, chain: base, transport: http() });
console.log('Wallet:', account.address);

// ─── Discover available filenames from catalog ────────────────────────────────
async function fetchCatalog() {
  const res = await fetch(BASE_URL, { headers: { 'Accept': 'application/agent+json' } });
  if (!res.ok) throw new Error(`Catalog fetch failed: ${res.status}`);
  const data = await res.json();
  return data?.data_marketplace?.files ?? [];
}

function latestFileForPrefix(files, prefix, extension) {
  const matches = files
    .filter(f => f.filename.startsWith(prefix) && f.filename.endsWith(`.${extension}`))
    .sort((a, b) => b.filename.localeCompare(a.filename));
  return matches[0]?.filename ?? null;
}

// ─── EIP-712 payment header ───────────────────────────────────────────────────
async function buildPaymentHeader(spec) {
  const raw = spec.accepts[0];
  const nonce       = toHex(crypto.getRandomValues(new Uint8Array(32)));
  const validAfter  = '0';
  const validBefore = String(Math.floor(Date.now() / 1000) + raw.maxTimeoutSeconds);

  const signature = await walletClient.signTypedData({
    domain: {
      name:              raw.extra?.name    ?? 'USD Coin',
      version:           raw.extra?.version ?? '2',
      chainId:           8453,
      verifyingContract: getAddress(raw.asset),
    },
    types: {
      TransferWithAuthorization: [
        { name: 'from',        type: 'address' },
        { name: 'to',          type: 'address' },
        { name: 'value',       type: 'uint256' },
        { name: 'validAfter',  type: 'uint256' },
        { name: 'validBefore', type: 'uint256' },
        { name: 'nonce',       type: 'bytes32' },
      ],
    },
    primaryType: 'TransferWithAuthorization',
    message: {
      from:        getAddress(account.address),
      to:          getAddress(raw.payTo),
      value:       BigInt(raw.amount),
      validAfter:  BigInt(validAfter),
      validBefore: BigInt(validBefore),
      nonce,
    },
  });

  const paymentPayload = {
    x402Version: spec.x402Version ?? 2,
    payload: {
      authorization: {
        from: account.address, to: raw.payTo, value: raw.amount,
        validAfter, validBefore, nonce,
      },
      signature,
    },
    accepted: { ...raw, maxAmountRequired: raw.amount },
  };

  return Buffer.from(JSON.stringify(paymentPayload)).toString('base64');
}

// ─── Purchase one file ────────────────────────────────────────────────────────
async function purchaseFile(filename) {
  const url = `${BASE_URL}/data/${filename}`;
  console.log(`\nFetching: ${url}`);

  const r1 = await fetch(url);
  console.log('Initial status:', r1.status);

  if (r1.status === 200) {
    console.log('Available without payment.');
    return { data: await r1.text(), paid: null };
  }
  if (r1.status === 404) {
    return null;
  }
  if (r1.status !== 402) {
    throw new Error(`Unexpected ${r1.status}: ${await r1.text()}`);
  }

  // Parse 402 payment spec
  let spec;
  const ct = r1.headers.get('content-type') ?? '';
  if (ct.includes('application/json') || ct.includes('text/')) {
    const text = await r1.text();
    try { spec = JSON.parse(text); }
    catch { throw new Error(`Non-JSON 402 body: ${text}`); }
  } else {
    const hdr = r1.headers.get('payment-required') ?? r1.headers.get('x-payment-required');
    if (!hdr) throw new Error('No payment spec in 402 response');
    spec = JSON.parse(Buffer.from(hdr, 'base64').toString('utf8'));
  }

  const raw = spec.accepts[0];
  const amountUsdc = (Number(raw.amount) / 1e6).toFixed(4);
  console.log(`Paying $${amountUsdc} USDC → ${raw.payTo}`);

  const payment = await buildPaymentHeader(spec);

  const r2 = await fetch(url, {
    headers: { 'PAYMENT-SIGNATURE': payment },
  });

  console.log('Paid status:', r2.status);

  const xpr = r2.headers.get('X-PAYMENT-RESPONSE');
  if (xpr) {
    try { console.log('Payment response:', JSON.stringify(JSON.parse(Buffer.from(xpr, 'base64').toString()), null, 2)); }
    catch { /* ignore */ }
  }

  if (r2.status !== 200) {
    throw new Error(`Payment rejected (${r2.status}): ${await r2.text()}`);
  }

  return { data: await r2.text(), paid: raw.amount };
}

// ─── Main ─────────────────────────────────────────────────────────────────────
const publicDir = join(__dirname, '..', 'public');
mkdirSync(publicDir, { recursive: true });

console.log('\nFetching catalog from Well Knowns...');
const catalog = await fetchCatalog();
console.log(`Found ${catalog.length} files in catalog.`);

let totalPaid = 0n;

// Purchase agent index
console.log('\n=== Purchasing agent-index ===');
const agentFilename = latestFileForPrefix(catalog, 'agent-index', 'json');
if (!agentFilename) { console.error('No agent-index file found in catalog.'); process.exit(1); }
console.log(`Latest: ${agentFilename}`);
const agentResult = await purchaseFile(agentFilename);
if (!agentResult) { console.error('Purchase returned null.'); process.exit(1); }
const agentDate = agentFilename.match(/(\d{4}-\d{2}-\d{2})/)?.[1] ?? 'unknown';
const agentOut = join(publicDir, `wellknowns-agent-index-${agentDate}.json`);
writeFileSync(agentOut, agentResult.data, 'utf8');
console.log(`✓ Saved → ${agentOut}`);
if (agentResult.paid) {
  totalPaid += BigInt(agentResult.paid);
  console.log(`✓ Paid: $${(Number(agentResult.paid) / 1e6).toFixed(4)} USDC`);
}

// Purchase MCP infrastructure
console.log('\n=== Purchasing mcp-infrastructure ===');
const mcpFilename = latestFileForPrefix(catalog, 'mcp-infrastructure', 'json');
if (!mcpFilename) { console.error('No mcp-infrastructure file found in catalog.'); process.exit(1); }
console.log(`Latest: ${mcpFilename}`);
const mcpResult = await purchaseFile(mcpFilename);
if (!mcpResult) { console.error('Purchase returned null.'); process.exit(1); }
const mcpDate = mcpFilename.match(/(\d{4}-\d{2}-\d{2})/)?.[1] ?? 'unknown';
const mcpOut = join(publicDir, `wellknowns-mcp-infra-${mcpDate}.json`);
writeFileSync(mcpOut, mcpResult.data, 'utf8');
console.log(`✓ Saved → ${mcpOut}`);
if (mcpResult.paid) {
  totalPaid += BigInt(mcpResult.paid);
  console.log(`✓ Paid: $${(Number(mcpResult.paid) / 1e6).toFixed(4)} USDC`);
}

console.log(`\n=== Total spent: $${(Number(totalPaid) / 1e6).toFixed(4)} USDC ===`);

// Preview first entry from each
const firstAgent = agentResult.data.startsWith('[')
  ? JSON.parse(agentResult.data)[0]
  : JSON.parse(agentResult.data.trim().split('\n')[0]);
console.log('\nSample agent-index entry:', JSON.stringify(firstAgent, null, 2));

const firstMcp = mcpResult.data.startsWith('[')
  ? JSON.parse(mcpResult.data)[0]
  : JSON.parse(mcpResult.data.trim().split('\n')[0]);
console.log('\nSample mcp-infrastructure entry:', JSON.stringify(firstMcp, null, 2));
