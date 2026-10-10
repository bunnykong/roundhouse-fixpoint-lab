/* This walk allocates nothing; its caller roots the input graph. */
static sp_int j_sum(sp_RbVal value) {
  if (value.tag == SP_TAG_INT) return value.v.i;
  if (value.tag != SP_TAG_OBJ) return 0;
  sp_int sum = 0;
  if (sp_poly_is_hash_kind(value.cls_id)) {
    sp_int n = j_hash_len(value);
    for (sp_int i = 0; i < n; i++) {
      sp_RbVal k, v;
      sp_poly_hash_pair(value, i, &k, &v);
      sum = sp_int_add(sum, j_sum(v));
    }
    return sum;
  }
  if (sp_poly_is_array_kind(value.cls_id)) {
    sp_int n = sp_poly_arr_len(value);
    for (sp_int i = 0; i < n; i++) sum = sp_int_add(sum, j_sum(sp_poly_arr_get(value, i)));
    return sum;
  }
  abort();
}
static inline sp_RbVal sp_rb_sum_leaves(sp_RbVal value) {
  return sp_box_int(j_sum(value));
}
