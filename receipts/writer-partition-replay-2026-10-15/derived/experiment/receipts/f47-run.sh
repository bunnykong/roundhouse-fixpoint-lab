#!/usr/bin/env bash
# The caller holds the shared workshop lock across this sequential phase.
set -euo pipefail
cd "$(dirname "$0")"
source ./setup.sh
case "${1:?phase required}" in
  baseline)
    RBENV_VERSION=4.0.7 ruby -c "$C/src/analyze/fixpoint_bound/fixtures/reflective_containers.rb"
    python3 -B run_laws.py baseline-native-array writer_law_bound_reflective_native_array_entrance --expected-exit 101
    python3 -B run_laws.py baseline-containers writer_law_bound_reflective_container_ --expected-exit 101
    ;;
  checks)
    python3 -B run_laws.py reflect-off writer_law_reflective_ivar_bound --flag 0 --expected-exit 101
    python3 -B run_laws.py reflect-on writer_law_reflective_ivar_bound
    python3 -B run_laws.py batch-off writer_law_ivar_batch_bound --flag 0
    python3 -B run_laws.py batch-on writer_law_ivar_batch_bound
    python3 -B run_laws.py entrances-off writer_law_bound_reflective_ --flag 0 --expected-exit 101
    python3 -B run_laws.py entrances-on writer_law_bound_reflective_
    python3 -B run_laws.py membership-on writer_law_bound_membership_canaries
    python3 -B run_laws.py partitions-on writer_law_bound_partitions --expected-exit 101
    python3 -B run_laws.py pairwise-off writer_law_bound_ivar_schedule --flag 0 --expected-exit 101
    python3 -B run_laws.py pairwise-on writer_law_bound_ivar_schedule --expected-exit 101
    python3 -B run_laws.py parameter-schedule writer_law_bound_param_schedule --expected-exit 101
    python3 -B run_laws.py boundary-on writer_law_bound_idempotence_and_pending
    RBENV_VERSION=4.0.7 ruby reproduce_containers.rb > evidence/runtime-containers.json
    ;;
  integration)
    python3 -B prepare_fixtures.py
    python3 -B run_laws.py default-lib-on unused --default || true
    for suite in analyze ingest real_blog runtime_src_integration lowered_ruby_emit; do
      python3 -B run_laws.py "integration-$suite-on" unused --default --integration "$suite" || true
    done
    ;;
  exports)
    python3 -B prepare_exports.py
    python3 -B "$BOUND/experiments/f19_check.py" --output "$BOUND/results/f19-bound-v1" \
      --candidate-env RH_REFLECT_BOUND=1
    for app in campfire mastodon chatwoot forem discourse; do
      python3 -B "$BOUND/experiments/app_check.py" --app "$app" \
        --output "$BOUND/results/$app-bound-v1" --candidate-env RH_REFLECT_BOUND=1
    done
    python3 -B f29_check.py
    ;;
  parity)
    python3 -B parity_check.py
    ;;
  verify)
    python3 -B verify_r2.py
    python3 -B assess_integration.py
    ;;
  clean)
    python3 -B clean.py
    ;;
  *) exit 2 ;;
esac
