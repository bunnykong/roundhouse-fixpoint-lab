static inline sp_RbVal sp_canonical(sp_RbVal value) {
  SP_GC_SAVE();
  SP_GC_ROOT_RBVAL(value);
  if (value.tag != SP_TAG_OBJ) return value;
  if (sp_poly_is_hash_kind(value.cls_id)) {
    sp_StrArray *keys = sp_StrArray_new(); SP_GC_ROOT(keys);
    sp_int n = j_hash_len(value);
    for (sp_int i = 0; i < n; i++) {
      sp_RbVal k, v;
      sp_poly_hash_pair(value, i, &k, &v);
      if (k.tag != SP_TAG_STR) abort();
      sp_StrArray_push(keys, k.v.s);
    }
    sp_StrArray_sort_bang(keys);
    sp_StrPolyHash *out = sp_StrPolyHash_new(); SP_GC_ROOT(out);
    for (sp_int i = 0; i < keys->len; i++) {
      const char *k = keys->data[i];
      sp_RbVal v = sp_canonical(j_hash_get(value, k));
      SP_GC_ROOT_RBVAL(v);
      sp_StrPolyHash_set(out, k, v);
    }
    return sp_box_obj(out, SP_BUILTIN_STR_POLY_HASH);
  }
  if (sp_poly_is_array_kind(value.cls_id)) {
    sp_PolyArray *out = sp_PolyArray_new(); SP_GC_ROOT(out);
    sp_int n = sp_poly_arr_len(value);
    for (sp_int i = 0; i < n; i++) {
      sp_RbVal v = sp_canonical(sp_poly_arr_get(value, i));
      SP_GC_ROOT_RBVAL(v);
      sp_PolyArray_push(out, v);
    }
    return sp_box_poly_array(out);
  }
  abort();
}
