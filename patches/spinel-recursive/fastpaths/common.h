/* Experimental closed JSON domain: builtin containers, String keys, no overrides/default procs.
 * Reuses Spinel's layout and GC. This is a manually specialized lowerer, not a compiler feature.
 */
static sp_int j_hash_len(sp_RbVal v) {
  switch (v.cls_id) {
  case SP_BUILTIN_STR_POLY_HASH: return ((sp_StrPolyHash *)v.v.p)->len;
  case SP_BUILTIN_STR_INT_HASH: return ((sp_StrIntHash *)v.v.p)->len;
  case SP_BUILTIN_STR_STR_HASH: return ((sp_StrStrHash *)v.v.p)->len;
  case SP_BUILTIN_POLY_POLY_HASH: return ((sp_PolyPolyHash *)v.v.p)->len;
  case SP_BUILTIN_INT_INT_HASH:
    if (((sp_IntIntHash *)v.v.p)->len == 0) return 0; /* empty Hash's default layout */
    abort();
  default: abort();
  }
}
static sp_RbVal j_hash_get(sp_RbVal v, const char *key) {
  switch (v.cls_id) {
  case SP_BUILTIN_STR_POLY_HASH: return sp_StrPolyHash_get((sp_StrPolyHash *)v.v.p, key);
  case SP_BUILTIN_STR_INT_HASH: return sp_box_int(sp_StrIntHash_get((sp_StrIntHash *)v.v.p, key));
  case SP_BUILTIN_STR_STR_HASH: return sp_box_str(sp_StrStrHash_get((sp_StrStrHash *)v.v.p, key));
  case SP_BUILTIN_POLY_POLY_HASH: return sp_PolyPolyHash_get((sp_PolyPolyHash *)v.v.p, sp_box_str(key));
  default: abort();
  }
}
