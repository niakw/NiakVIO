// SPDX-License-Identifier: GPL-3.0-only
'use strict';

/**
 * Availability is not an acceptance test. A single correct-catalogue work
 * returning no provider-owned request is an inconclusive diagnostic, not a
 * provider-domain/transport failure. One different work in the SAME
 * canonical catalogue class distinguishes title selection from a generic
 * pre-network gate while staying cheap (one extra probe per provider).
 */
function shouldRetryNoRequest(primaryResults, category) {
  const rows = (primaryResults || []).filter(row =>
    row && row.fixture && row.fixture.category === category);
  return rows.length > 0 && rows.every(row =>
    row.status === 'provider_unreachable'
    && row.failure_class === 'no_provider_request_observed'
    && !(row.runtime_errors || []).length);
}

module.exports = { shouldRetryNoRequest };
