#!/bin/bash
# Dispatch to PSC Bridges-2 from Delta. Delta is canonical: code reaches Bridges-2 by `git pull` of the
# pushed branch, data by rsync pushed from Delta, and results come back by rsync pulled from Delta.
# Every transfer runs on Delta; nothing on Bridges-2 ever writes to Delta. See docs/bridges2.md.
#
#   scripts/remote/b2.sh sync-code  [--dry] [--branch NAME]
#   scripts/remote/b2.sh sync-data  [--dry] [-n] [--what model,wikitext,env,runs|all]
#   scripts/remote/b2.sh unpack-env [--dry]
#   scripts/remote/b2.sh submit     [--dry] [--test-only] [--time HH:MM:SS] [--script PATH] [--job-name N] -- ARGS...
#   scripts/remote/b2.sh status     [--dry] [JOBID...]
#   scripts/remote/b2.sh fetch      [--dry] [-n] [--ignore-existing] [REPO_RELATIVE_PATH...]
#
# --dry prints each command ('+ ...') and runs nothing, not even the SSH master check.
# -n passes --dry-run to rsync (needs the masters; shows what would transfer).
# The branch sync-code checks out is --branch, else DC_B2_BRANCH, else mechanism-datasets.
#
# SSH: the aliases `bridges2` (login, Slurm) and `b2dtn` (data.bridges2.psc.edu, transfers) multiplex over
# ControlMaster sockets the user opens by hand. This script never authenticates: it checks the master with
# `ssh -O check` first and runs every ssh with BatchMode=yes, so a closed master is an error, not a prompt.
#
# Profiles: scripts/cluster/delta.env (local paths) and scripts/cluster/bridges2.env (remote paths, account,
# GPU). Tests override them with DC_DELTA_PROFILE / DC_B2_PROFILE / DC_B2_MANIFEST.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BRANCH="${DC_B2_BRANCH:-mechanism-datasets}"
REMOTE_URL="https://github.com/JaMussCraft/Deception-Circuit.git"
LOGIN_HOST="bridges2"
DTN_HOST="b2dtn"
ENV_PACK="${DC_ENV_PACK:-/work/nvme/beto/swong2/envs/mgnp-conda-pack.tar.gz}"
MANIFEST="${DC_B2_MANIFEST:-$HERE/scripts/remote/b2_manifest.txt}"
# HF cache subdirs to copy. Never the HF_HOME root: it holds the hub token.
HF_MODEL_DIRS=("hub/models--meta-llama--Llama-3.1-8B-Instruct")
HF_WIKITEXT_DIRS=("hub/datasets--Salesforce--wikitext" "datasets/Salesforce___wikitext")
# Suite output roots that `fetch` brings back whole (ticket 06 writes its suites under the second).
FETCH_SUITE_ROOTS=("outputs/_suites" "outputs/_launch_mechanism_v2/evals")
# Analysis cells under outputs/_analyses that `fetch` brings back (git-ignored, so a fetch is their only way
# to Delta). Only these: the v1 cells of record in the same directory are never touched.
FETCH_ANALYSIS_GLOBS=("mechanism-analysis-*")

usage() {
    cat >&2 <<'EOF'
usage: scripts/remote/b2.sh sync-code  [--dry] [--branch NAME]
       scripts/remote/b2.sh sync-data  [--dry] [-n] [--what model,wikitext,env,runs|all]
       scripts/remote/b2.sh unpack-env [--dry]
       scripts/remote/b2.sh submit     [--dry] [--test-only] [--time HH:MM:SS] [--script PATH] [--job-name N] -- ARGS...
       scripts/remote/b2.sh status     [--dry] [JOBID...]
       scripts/remote/b2.sh fetch      [--dry] [-n] [--ignore-existing] [REPO_RELATIVE_PATH...]
The branch sync-code checks out is --branch, else DC_B2_BRANCH, else mechanism-datasets.
See docs/bridges2.md.
EOF
    exit 2
}

# --- profiles --------------------------------------------------------------------------------------------
source "${DC_DELTA_PROFILE:-$HERE/scripts/cluster/delta.env}"
LOCAL_REPO="$DC_REPO_ROOT"
LOCAL_HF="$DC_HF_HOME"
source "${DC_B2_PROFILE:-$HERE/scripts/cluster/bridges2.env}"
B2_ALLOC="$DC_B2_ALLOC"
B2_PROJECT="$DC_B2_PROJECT"
B2_REPO="$DC_REPO_ROOT"
B2_HF="$DC_HF_HOME"
B2_ENV_PREFIX="$DC_ENV_PREFIX"
B2_ACCOUNT="$DC_ACCOUNT"
B2_PARTITION="$DC_PARTITION"
B2_GPU_SPEC="$DC_GPU_SPEC"
B2_TIME="$DC_TIME_DEFAULT"

# --- options ---------------------------------------------------------------------------------------------
[ "$#" -ge 1 ] || usage
SUB="$1"; shift
DRY=0; RSYNC_N=(); WHAT="model,wikitext,runs"; TEST_ONLY=(); SCRIPT="scripts/evaluate_circuit.sbatch"
JOB_NAME=(); UPDATE_MODE="--update"; POS=()
while [ "$#" -gt 0 ]; do
    case "$1" in
        --dry) DRY=1 ;;
        -n|--rsync-dry-run) RSYNC_N=(--dry-run) ;;
        --what) WHAT="$2"; shift ;;
        --test-only) TEST_ONLY=(--test-only) ;;
        --time) B2_TIME="$2"; shift ;;
        --script) SCRIPT="$2"; shift ;;
        --job-name) JOB_NAME=("--job-name=$2"); shift ;;
        --ignore-existing) UPDATE_MODE="--ignore-existing" ;;
        --branch) BRANCH="$2"; shift ;;
        --) shift; POS+=("$@"); break ;;
        -h|--help) usage ;;
        *) POS+=("$1") ;;
    esac
    shift
done
[ "$WHAT" = "all" ] && WHAT="model,wikitext,env,runs"
# The branch goes into a remote shell command: a plain ref name only.
if ! [[ "$BRANCH" =~ ^[A-Za-z0-9][A-Za-z0-9._/-]*$ ]]; then
    echo "b2.sh: branch '$BRANCH' is not a plain ref name (letters, digits, . _ / -)" >&2
    exit 2
fi

# --- helpers ---------------------------------------------------------------------------------------------
die() { echo "b2.sh: $*" >&2; exit 1; }

# Print a command readably: words that need it are single-quoted.
show() {
    local out="+" w
    for w in "$@"; do
        if [[ "$w" =~ ^[A-Za-z0-9_./:=,@+%*~-]+$ ]]; then out+=" $w"; else out+=" '${w//\'/\'\\\'\'}'"; fi
    done
    echo "$out"
}

run() { show "$@"; [ "$DRY" = 1 ] || "$@"; }

need_master() {
    [ "$DRY" = 1 ] && return 0
    if ! ssh -O check "$1" >/dev/null 2>&1; then
        die "no SSH master for '$1' on $(hostname -s). Open it by hand on this login node (it asks for the PSC password):  ssh -fN $1   (see docs/bridges2.md)"
    fi
}

need_alloc() {
    case "$B2_ALLOC" in
        ""|*__ALLOC__*) die "Bridges-2 allocation is still the placeholder __ALLOC__ in scripts/cluster/bridges2.env; run 'projects' on Bridges-2 and fill DC_B2_ALLOC" ;;
    esac
}

SSH=(ssh -o BatchMode=yes)
RSYNC_COMMON=(--partial --human-readable --itemize-changes -e "ssh -o BatchMode=yes"
              --exclude=token --exclude=.bashrc "--exclude=*.lock")
RSYNC=(rsync -a "${RSYNC_COMMON[@]}")

# Refuse anything that looks like a credential, an absolute path or a path out of the repo.
check_manifest_path() {
    case "$1" in
        /*|"~"*|*..*) die "manifest path must be repo-relative: $1" ;;
    esac
    case "$1" in
        *.bashrc*|*.bash_profile*|*token*|*key*|*.ssh*|*.netrc*|*secret*) die "refusing to copy a possible secret: $1" ;;
    esac
}

remote_q() { printf '%q ' "$@"; }

# --- subcommands -----------------------------------------------------------------------------------------
case "$SUB" in
sync-code)
    [ "$DRY" = 1 ] || need_alloc
    need_master "$LOGIN_HOST"
    parent="$(dirname "$B2_REPO")"
    cmd="export GIT_TERMINAL_PROMPT=0; set -e; if [ -d $B2_REPO/.git ]; then"
    # Forced refspec (+): a force-pushed branch still updates the remote-tracking ref.
    cmd+=" git -C $B2_REPO fetch origin +$BRANCH:refs/remotes/origin/$BRANCH;"
    # A clone that has never had the branch makes a tracking branch from the one just fetched. Whether the
    # branch exists is asked first, so a checkout that fails for a real reason (local edits in the way) stops
    # here with git's own message.
    cmd+=" if git -C $B2_REPO show-ref --verify --quiet refs/heads/$BRANCH;"
    cmd+=" then git -C $B2_REPO checkout $BRANCH;"
    cmd+=" else git -C $B2_REPO checkout -b $BRANCH --track origin/$BRANCH; fi;"
    # Fast-forward. After a force-push that is impossible: the clone never carries commits of its own (code
    # reaches it only from origin), so the branch moves to origin's head with reset --keep, which keeps
    # uncommitted edits and refuses if they are in the way. The old head is printed for recovery.
    cmd+=" if ! git -C $B2_REPO merge --ff-only origin/$BRANCH; then"
    cmd+=" echo \"b2.sh: origin/$BRANCH is not a fast-forward of $BRANCH (force-pushed?); moving $BRANCH from"
    cmd+=" \$(git -C $B2_REPO rev-parse HEAD) to \$(git -C $B2_REPO rev-parse origin/$BRANCH)\" >&2;"
    cmd+=" git -C $B2_REPO reset --keep origin/$BRANCH; fi;"
    cmd+=" else mkdir -p $parent && git clone --branch $BRANCH $REMOTE_URL $B2_REPO; fi;"
    cmd+=" git -C $B2_REPO status --short --untracked-files=no; echo remote_head=\$(git -C $B2_REPO rev-parse HEAD)"
    run "${SSH[@]}" "$LOGIN_HOST" "$cmd"
    if [ "$DRY" = 0 ]; then
        echo "local_head=$(git -C "$LOCAL_REPO" rev-parse HEAD)  (Bridges-2 sees only what is pushed to origin/$BRANCH)"
    fi
    ;;

sync-data)
    [ "$DRY" = 1 ] || need_alloc
    need_master "$DTN_HOST"
    need_master "$LOGIN_HOST"
    # The transfer host runs rsync without a shell (no `mkdir && rsync` via --rsync-path), so the target
    # dirs are created through the login host, which mounts the same /ocean.
    run "${SSH[@]}" "$LOGIN_HOST" "mkdir -p $B2_HF $B2_PROJECT/envs $B2_REPO"
    IFS=',' read -r -a parts <<< "$WHAT"
    for part in "${parts[@]}"; do
        case "$part" in
            model|wikitext)
                if [ "$part" = model ]; then dirs=("${HF_MODEL_DIRS[@]}"); else dirs=("${HF_WIKITEXT_DIRS[@]}"); fi
                for d in "${dirs[@]}"; do
                    run "${RSYNC[@]}" "${RSYNC_N[@]}" --relative "$LOCAL_HF/./$d/" "$DTN_HOST:$B2_HF/"
                done ;;
            env)
                [ "$DRY" = 1 ] || [ -f "$ENV_PACK" ] || die "conda-pack tarball not found: $ENV_PACK"
                run "${RSYNC[@]}" "${RSYNC_N[@]}" "$ENV_PACK" "$DTN_HOST:$B2_PROJECT/envs/" ;;
            runs)
                paths=()
                while IFS= read -r line || [ -n "$line" ]; do
                    line="${line%%#*}"; line="${line//[[:space:]]/}"
                    [ -n "$line" ] || continue
                    check_manifest_path "$line"
                    paths+=("$LOCAL_REPO/./$line/")
                done < "$MANIFEST"
                [ "${#paths[@]}" -gt 0 ] || die "manifest $MANIFEST lists no paths"
                run "${RSYNC[@]}" "${RSYNC_N[@]}" --relative --exclude=history.json --exclude=train.log \
                    "${paths[@]}" "$DTN_HOST:$B2_REPO/" ;;
            *) die "unknown --what part: $part (model, wikitext, env, runs, all)" ;;
        esac
    done
    ;;

unpack-env)
    [ "$DRY" = 1 ] || need_alloc
    need_master "$LOGIN_HOST"
    pack="$B2_PROJECT/envs/$(basename "$ENV_PACK")"
    cmd="set -e; mkdir -p $B2_ENV_PREFIX; tar -xzf $pack -C $B2_ENV_PREFIX;"
    cmd+=" source $B2_ENV_PREFIX/bin/activate; conda-unpack;"
    cmd+=" python -c 'import torch, transformers, datasets, accelerate; print(torch.__version__, transformers.__version__, datasets.__version__, accelerate.__version__)'"
    run "${SSH[@]}" "$LOGIN_HOST" "$cmd"
    ;;

submit)
    need_alloc
    need_master "$LOGIN_HOST"
    [ "${#POS[@]}" -gt 0 ] || [ "$SCRIPT" != "scripts/evaluate_circuit.sbatch" ] || die "submit needs arguments for $SCRIPT after --"
    # Bridges-2 login nodes set SBATCH_EXPORT=NONE, so variables in the submit environment never reach the
    # job. --export=ALL (Delta's default) plus the profile selection makes the job source this profile with
    # this allocation even if the clone's bridges2.env is older.
    cmd="cd $B2_REPO && mkdir -p logs && sbatch --export=ALL,DC_CLUSTER=bridges2,DC_B2_ALLOC=$B2_ALLOC -A $B2_ACCOUNT -p $B2_PARTITION $B2_GPU_SPEC -t $B2_TIME"
    [ "${#TEST_ONLY[@]}" -eq 0 ] || cmd+=" --test-only"
    [ "${#JOB_NAME[@]}" -eq 0 ] || cmd+=" $(remote_q "${JOB_NAME[@]}")"
    cmd+=" $SCRIPT"
    [ "${#POS[@]}" -eq 0 ] || cmd+=" $(remote_q "${POS[@]}")"
    run "${SSH[@]}" "$LOGIN_HOST" "${cmd% }"
    ;;

status)
    need_master "$LOGIN_HOST"
    if [ "${#POS[@]}" -gt 0 ]; then
        ids="$(IFS=,; echo "${POS[*]}")"
        cmd="sacct -X -j $ids -o JobID,JobName%24,Partition,State,Elapsed,AllocTRES%48"
    else
        cmd="squeue -u \$USER; sacct -X -u \$USER -S now-2days -o JobID,JobName%24,Partition,State,Elapsed,AllocTRES%48"
    fi
    run "${SSH[@]}" "$LOGIN_HOST" "$cmd"
    ;;

fetch)
    need_master "$DTN_HOST"
    # Never --delete. --update keeps any Delta file newer than the Bridges-2 copy; --ignore-existing keeps
    # every Delta file that already exists (use it for immutable cell outputs). --checksum skips files whose
    # bytes already match (a Bridges-2 clone gives tracked files fresh mtimes), and any Delta file that is
    # still replaced is kept next to it as <name>.pre-b2fetch. -rl, not -a: no Bridges-2 perms, times, group or
    # owner land on Delta, so identical files stay untouched and new files get Delta's default (setgid group)
    # permissions and their arrival time.
    FETCH=(rsync -rl --no-perms --no-times --no-group --no-owner "${RSYNC_COMMON[@]}" "${RSYNC_N[@]}"
           --checksum "$UPDATE_MODE" --backup --suffix=.pre-b2fetch)
    [ "$UPDATE_MODE" = "--update" ] || FETCH+=(--update)
    fetch_one() {  # remote-relative path, filter args...
        local p="$1"; shift
        # Only the parent: rsync creates the last component itself, so a path missing on Bridges-2 leaves
        # no empty dir on Delta.
        [ "$DRY" = 1 ] || mkdir -p "$(dirname "$LOCAL_REPO/$p")"
        run "${FETCH[@]}" "$@" "$DTN_HOST:$B2_REPO/$p/" "$LOCAL_REPO/$p/" \
            || echo "b2.sh: warning: fetch of $p failed or it does not exist on Bridges-2 (rsync exit $?)" >&2
    }
    if [ "${#POS[@]}" -eq 0 ]; then
        # Default: evaluations*/ under every manifest run dir, the suite roots, and the Slurm logs (into
        # logs/bridges2/). Nothing else under outputs/, so tracked v1 results are never touched.
        while IFS= read -r line || [ -n "$line" ]; do
            line="${line%%#*}"; line="${line//[[:space:]]/}"
            [ -n "$line" ] || continue
            check_manifest_path "$line"
            fetch_one "$line" --prune-empty-dirs "--include=evaluations*/***" "--exclude=*"
        done < "$MANIFEST"
        for root in "${FETCH_SUITE_ROOTS[@]}"; do fetch_one "$root"; done
        ana_filter=()
        for glob in "${FETCH_ANALYSIS_GLOBS[@]}"; do ana_filter+=("--include=/$glob/***"); done
        fetch_one "outputs/_analyses" --prune-empty-dirs "${ana_filter[@]}" "--exclude=*"
        [ "$DRY" = 1 ] || mkdir -p "$LOCAL_REPO/logs/bridges2"
        run "${FETCH[@]}" "$DTN_HOST:$B2_REPO/logs/" "$LOCAL_REPO/logs/bridges2/" \
            || echo "b2.sh: warning: fetch of logs/ failed (rsync exit $?)" >&2
    else
        for p in "${POS[@]}"; do
            check_manifest_path "$p"
            fetch_one "$p"
        done
    fi
    ;;

*) usage ;;
esac
