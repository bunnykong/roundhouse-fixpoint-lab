class TreesController < ApplicationController
  def index
    @tree = [f0, f1, f2, f3, f4, f5, f6, f7, f8, f9, f10, f11, f12, f13, f14, f15, f16, f17, f18, f19, f20, f21, f22, f23, f24, f25, f26, f27, f28, f29, f30, f31, f32, f33, f34, f35, f36, f37, f38, f39, f40, f41, f42, f43, f44, f45, f46, f47, f48, f49, f50, f51, f52, f53, f54, f55, f56, f57, f58, f59, f60, f61, f62, f63, f64, f65, f66, f67, f68, f69, f70, f71, f72, f73, f74, f75, f76, f77, f78, f79, f80, f81, f82, f83, f84, f85, f86, f87, f88, f89, f90, f91, f92, f93, f94, f95, f96, f97, f98, f99, f100, f101, f102, f103, f104, f105, f106, f107, f108, f109, f110, f111, f112, f113, f114, f115, f116, f117, f118, f119, f120, f121, f122, f123, f124, f125, f126, f127, f128, f129, f130, f131, f132, f133, f134, f135, f136, f137, f138, f139, f140, f141, f142, f143, f144, f145, f146, f147, f148, f149, f150, f151, f152, f153, f154, f155, f156, f157, f158, f159, f160, f161, f162, f163, f164, f165, f166, f167, f168, f169, f170, f171, f172, f173, f174, f175, f176, f177, f178, f179, f180, f181, f182, f183, f184, f185, f186, f187, f188, f189, f190, f191, f192, f193, f194, f195, f196, f197, f198, f199, f200, f201, f202, f203, f204, f205, f206, f207, f208, f209, f210, f211, f212, f213, f214, f215, f216, f217, f218, f219, f220, f221, f222, f223, f224, f225, f226, f227, f228, f229, f230, f231, f232, f233, f234, f235, f236, f237, f238, f239, f240, f241, f242, f243, f244, f245, f246, f247, f248, f249, f250, f251, f252, f253, f254, f255, f256, f257, f258, f259, f260, f261, f262, f263, f264, f265, f266, f267, f268, f269, f270, f271, f272, f273, f274, f275, f276, f277, f278, f279, f280, f281, f282, f283, f284, f285, f286, f287, f288, f289, f290, f291, f292, f293, f294, f295, f296, f297, f298, f299, f300, f301, f302, f303, f304, f305, f306, f307, f308, f309, f310, f311, f312, f313, f314, f315, f316, f317, f318, f319, f320, f321, f322, f323, f324, f325, f326, f327, f328, f329, f330, f331, f332, f333, f334, f335, f336, f337, f338, f339, f340, f341, f342, f343, f344, f345, f346, f347, f348, f349, f350, f351, f352, f353, f354, f355, f356, f357, f358, f359, f360, f361, f362, f363, f364, f365, f366, f367, f368, f369, f370, f371, f372, f373, f374, f375, f376, f377, f378, f379, f380, f381, f382, f383, f384, f385, f386, f387, f388, f389, f390, f391, f392, f393, f394, f395, f396, f397, f398, f399, f400, f401, f402, f403, f404, f405, f406, f407, f408, f409, f410, f411, f412, f413, f414, f415, f416, f417, f418, f419, f420, f421, f422, f423, f424, f425, f426, f427, f428, f429, f430, f431, f432, f433, f434, f435, f436, f437, f438, f439, f440, f441, f442, f443, f444, f445, f446, f447, f448, f449, f450, f451, f452, f453, f454, f455, f456, f457, f458, f459, f460, f461, f462, f463, f464, f465, f466, f467, f468, f469, f470, f471, f472, f473, f474, f475, f476, f477, f478, f479, f480, f481, f482, f483, f484, f485, f486, f487, f488, f489, f490, f491, f492, f493, f494, f495, f496, f497, f498, f499, f500, f501, f502, f503, f504, f505, f506, f507, f508, f509, f510, f511, f512, f513, f514, f515, f516, f517, f518, f519, f520, f521, f522, f523, f524, f525, f526, f527, f528, f529, f530, f531]
  end

  private

  # hash each |a|
  def f0 = ({ "b" => 1, "c" => 2 }).each { |a| s0_a(a); nil }
  # hash each |a, b|
  def f1 = ({ "b" => 1, "c" => 2 }).each { |a, b| s1_a(a); s1_b(b); nil }
  # hash each |a, |
  def f2 = ({ "b" => 1, "c" => 2 }).each { |a, | s2_a(a); nil }
  # hash each |a, *r|
  def f3 = ({ "b" => 1, "c" => 2 }).each { |a, *r| s3_a(a); nil }
  # hash each |(a, b)|
  def f4 = ({ "b" => 1, "c" => 2 }).each { |(a, b)| s4_a(a); s4_b(b); nil }
  # hash each |(a, b), c|
  def f5 = ({ "b" => 1, "c" => 2 }).each { |(a, b), c| s5_a(a); s5_c(c); nil }
  # hash each |a, (b, c)|
  def f6 = ({ "b" => 1, "c" => 2 }).each { |a, (b, c)| s6_a(a); s6_c(c); nil }
  # hash map |a|
  def f7 = ({ "b" => 1, "c" => 2 }).map { |a| s7_a(a); nil }
  # hash map |a, b|
  def f8 = ({ "b" => 1, "c" => 2 }).map { |a, b| s8_a(a); s8_b(b); nil }
  # hash map |a, |
  def f9 = ({ "b" => 1, "c" => 2 }).map { |a, | s9_a(a); nil }
  # hash map |a, *r|
  def f10 = ({ "b" => 1, "c" => 2 }).map { |a, *r| s10_a(a); nil }
  # hash map |(a, b)|
  def f11 = ({ "b" => 1, "c" => 2 }).map { |(a, b)| s11_a(a); s11_b(b); nil }
  # hash map |(a, b), c|
  def f12 = ({ "b" => 1, "c" => 2 }).map { |(a, b), c| s12_a(a); s12_c(c); nil }
  # hash map |a, (b, c)|
  def f13 = ({ "b" => 1, "c" => 2 }).map { |a, (b, c)| s13_a(a); s13_c(c); nil }
  # hash select |a|
  def f14 = ({ "b" => 1, "c" => 2 }).select { |a| s14_a(a); true }
  # hash select |a, b|
  def f15 = ({ "b" => 1, "c" => 2 }).select { |a, b| s15_a(a); s15_b(b); true }
  # hash select |a, |
  def f16 = ({ "b" => 1, "c" => 2 }).select { |a, | s16_a(a); true }
  # hash select |a, *r|
  def f17 = ({ "b" => 1, "c" => 2 }).select { |a, *r| s17_a(a); true }
  # hash select |(a, b)|
  def f18 = ({ "b" => 1, "c" => 2 }).select { |(a, b)| s18_a(a); s18_b(b); true }
  # hash select |(a, b), c|
  def f19 = ({ "b" => 1, "c" => 2 }).select { |(a, b), c| s19_a(a); s19_c(c); true }
  # hash select |a, (b, c)|
  def f20 = ({ "b" => 1, "c" => 2 }).select { |a, (b, c)| s20_a(a); s20_c(c); true }
  # hash reject |a|
  def f21 = ({ "b" => 1, "c" => 2 }).reject { |a| s21_a(a); false }
  # hash reject |a, b|
  def f22 = ({ "b" => 1, "c" => 2 }).reject { |a, b| s22_a(a); s22_b(b); false }
  # hash reject |a, |
  def f23 = ({ "b" => 1, "c" => 2 }).reject { |a, | s23_a(a); false }
  # hash reject |a, *r|
  def f24 = ({ "b" => 1, "c" => 2 }).reject { |a, *r| s24_a(a); false }
  # hash reject |(a, b)|
  def f25 = ({ "b" => 1, "c" => 2 }).reject { |(a, b)| s25_a(a); s25_b(b); false }
  # hash reject |(a, b), c|
  def f26 = ({ "b" => 1, "c" => 2 }).reject { |(a, b), c| s26_a(a); s26_c(c); false }
  # hash reject |a, (b, c)|
  def f27 = ({ "b" => 1, "c" => 2 }).reject { |a, (b, c)| s27_a(a); s27_c(c); false }
  # hash each_with_index |a|
  def f28 = ({ "b" => 1, "c" => 2 }).each_with_index { |a| s28_a(a); nil }
  # hash each_with_index |a, b|
  def f29 = ({ "b" => 1, "c" => 2 }).each_with_index { |a, b| s29_a(a); s29_b(b); nil }
  # hash each_with_index |a, |
  def f30 = ({ "b" => 1, "c" => 2 }).each_with_index { |a, | s30_a(a); nil }
  # hash each_with_index |a, *r|
  def f31 = ({ "b" => 1, "c" => 2 }).each_with_index { |a, *r| s31_a(a); nil }
  # hash each_with_index |(a, b)|
  def f32 = ({ "b" => 1, "c" => 2 }).each_with_index { |(a, b)| s32_a(a); s32_b(b); nil }
  # hash each_with_index |(a, b), c|
  def f33 = ({ "b" => 1, "c" => 2 }).each_with_index { |(a, b), c| s33_a(a); s33_c(c); nil }
  # hash each_with_index |a, (b, c)|
  def f34 = ({ "b" => 1, "c" => 2 }).each_with_index { |a, (b, c)| s34_a(a); s34_c(c); nil }
  # hash sort_by |a|
  def f35 = ({ "b" => 1, "c" => 2 }).sort_by { |a| s35_a(a); 0 }
  # hash sort_by |a, b|
  def f36 = ({ "b" => 1, "c" => 2 }).sort_by { |a, b| s36_a(a); s36_b(b); 0 }
  # hash sort_by |a, |
  def f37 = ({ "b" => 1, "c" => 2 }).sort_by { |a, | s37_a(a); 0 }
  # hash sort_by |a, *r|
  def f38 = ({ "b" => 1, "c" => 2 }).sort_by { |a, *r| s38_a(a); 0 }
  # hash sort_by |(a, b)|
  def f39 = ({ "b" => 1, "c" => 2 }).sort_by { |(a, b)| s39_a(a); s39_b(b); 0 }
  # hash sort_by |(a, b), c|
  def f40 = ({ "b" => 1, "c" => 2 }).sort_by { |(a, b), c| s40_a(a); s40_c(c); 0 }
  # hash sort_by |a, (b, c)|
  def f41 = ({ "b" => 1, "c" => 2 }).sort_by { |a, (b, c)| s41_a(a); s41_c(c); 0 }
  # hash min_by |a|
  def f42 = ({ "b" => 1, "c" => 2 }).min_by { |a| s42_a(a); 0 }
  # hash min_by |a, b|
  def f43 = ({ "b" => 1, "c" => 2 }).min_by { |a, b| s43_a(a); s43_b(b); 0 }
  # hash min_by |a, |
  def f44 = ({ "b" => 1, "c" => 2 }).min_by { |a, | s44_a(a); 0 }
  # hash min_by |a, *r|
  def f45 = ({ "b" => 1, "c" => 2 }).min_by { |a, *r| s45_a(a); 0 }
  # hash min_by |(a, b)|
  def f46 = ({ "b" => 1, "c" => 2 }).min_by { |(a, b)| s46_a(a); s46_b(b); 0 }
  # hash min_by |(a, b), c|
  def f47 = ({ "b" => 1, "c" => 2 }).min_by { |(a, b), c| s47_a(a); s47_c(c); 0 }
  # hash min_by |a, (b, c)|
  def f48 = ({ "b" => 1, "c" => 2 }).min_by { |a, (b, c)| s48_a(a); s48_c(c); 0 }
  # hash group_by |a|
  def f49 = ({ "b" => 1, "c" => 2 }).group_by { |a| s49_a(a); 0 }
  # hash group_by |a, b|
  def f50 = ({ "b" => 1, "c" => 2 }).group_by { |a, b| s50_a(a); s50_b(b); 0 }
  # hash group_by |a, |
  def f51 = ({ "b" => 1, "c" => 2 }).group_by { |a, | s51_a(a); 0 }
  # hash group_by |a, *r|
  def f52 = ({ "b" => 1, "c" => 2 }).group_by { |a, *r| s52_a(a); 0 }
  # hash group_by |(a, b)|
  def f53 = ({ "b" => 1, "c" => 2 }).group_by { |(a, b)| s53_a(a); s53_b(b); 0 }
  # hash group_by |(a, b), c|
  def f54 = ({ "b" => 1, "c" => 2 }).group_by { |(a, b), c| s54_a(a); s54_c(c); 0 }
  # hash group_by |a, (b, c)|
  def f55 = ({ "b" => 1, "c" => 2 }).group_by { |a, (b, c)| s55_a(a); s55_c(c); 0 }
  # hash sum |a|
  def f56 = ({ "b" => 1, "c" => 2 }).sum { |a| s56_a(a); 0 }
  # hash sum |a, b|
  def f57 = ({ "b" => 1, "c" => 2 }).sum { |a, b| s57_a(a); s57_b(b); 0 }
  # hash sum |a, |
  def f58 = ({ "b" => 1, "c" => 2 }).sum { |a, | s58_a(a); 0 }
  # hash sum |a, *r|
  def f59 = ({ "b" => 1, "c" => 2 }).sum { |a, *r| s59_a(a); 0 }
  # hash sum |(a, b)|
  def f60 = ({ "b" => 1, "c" => 2 }).sum { |(a, b)| s60_a(a); s60_b(b); 0 }
  # hash sum |(a, b), c|
  def f61 = ({ "b" => 1, "c" => 2 }).sum { |(a, b), c| s61_a(a); s61_c(c); 0 }
  # hash sum |a, (b, c)|
  def f62 = ({ "b" => 1, "c" => 2 }).sum { |a, (b, c)| s62_a(a); s62_c(c); 0 }
  # hash filter_map |a|
  def f63 = ({ "b" => 1, "c" => 2 }).filter_map { |a| s63_a(a); nil }
  # hash filter_map |a, b|
  def f64 = ({ "b" => 1, "c" => 2 }).filter_map { |a, b| s64_a(a); s64_b(b); nil }
  # hash filter_map |a, |
  def f65 = ({ "b" => 1, "c" => 2 }).filter_map { |a, | s65_a(a); nil }
  # hash filter_map |a, *r|
  def f66 = ({ "b" => 1, "c" => 2 }).filter_map { |a, *r| s66_a(a); nil }
  # hash filter_map |(a, b)|
  def f67 = ({ "b" => 1, "c" => 2 }).filter_map { |(a, b)| s67_a(a); s67_b(b); nil }
  # hash filter_map |(a, b), c|
  def f68 = ({ "b" => 1, "c" => 2 }).filter_map { |(a, b), c| s68_a(a); s68_c(c); nil }
  # hash filter_map |a, (b, c)|
  def f69 = ({ "b" => 1, "c" => 2 }).filter_map { |a, (b, c)| s69_a(a); s69_c(c); nil }
  # hash flat_map |a|
  def f70 = ({ "b" => 1, "c" => 2 }).flat_map { |a| s70_a(a); [] }
  # hash flat_map |a, b|
  def f71 = ({ "b" => 1, "c" => 2 }).flat_map { |a, b| s71_a(a); s71_b(b); [] }
  # hash flat_map |a, |
  def f72 = ({ "b" => 1, "c" => 2 }).flat_map { |a, | s72_a(a); [] }
  # hash flat_map |a, *r|
  def f73 = ({ "b" => 1, "c" => 2 }).flat_map { |a, *r| s73_a(a); [] }
  # hash flat_map |(a, b)|
  def f74 = ({ "b" => 1, "c" => 2 }).flat_map { |(a, b)| s74_a(a); s74_b(b); [] }
  # hash flat_map |(a, b), c|
  def f75 = ({ "b" => 1, "c" => 2 }).flat_map { |(a, b), c| s75_a(a); s75_c(c); [] }
  # hash flat_map |a, (b, c)|
  def f76 = ({ "b" => 1, "c" => 2 }).flat_map { |a, (b, c)| s76_a(a); s76_c(c); [] }
  # hash count |a|
  def f77 = ({ "b" => 1, "c" => 2 }).count { |a| s77_a(a); true }
  # hash count |a, b|
  def f78 = ({ "b" => 1, "c" => 2 }).count { |a, b| s78_a(a); s78_b(b); true }
  # hash count |a, |
  def f79 = ({ "b" => 1, "c" => 2 }).count { |a, | s79_a(a); true }
  # hash count |a, *r|
  def f80 = ({ "b" => 1, "c" => 2 }).count { |a, *r| s80_a(a); true }
  # hash count |(a, b)|
  def f81 = ({ "b" => 1, "c" => 2 }).count { |(a, b)| s81_a(a); s81_b(b); true }
  # hash count |(a, b), c|
  def f82 = ({ "b" => 1, "c" => 2 }).count { |(a, b), c| s82_a(a); s82_c(c); true }
  # hash count |a, (b, c)|
  def f83 = ({ "b" => 1, "c" => 2 }).count { |a, (b, c)| s83_a(a); s83_c(c); true }
  # hash find |a|
  def f84 = ({ "b" => 1, "c" => 2 }).find { |a| s84_a(a); false }
  # hash find |a, b|
  def f85 = ({ "b" => 1, "c" => 2 }).find { |a, b| s85_a(a); s85_b(b); false }
  # hash find |a, |
  def f86 = ({ "b" => 1, "c" => 2 }).find { |a, | s86_a(a); false }
  # hash find |a, *r|
  def f87 = ({ "b" => 1, "c" => 2 }).find { |a, *r| s87_a(a); false }
  # hash find |(a, b)|
  def f88 = ({ "b" => 1, "c" => 2 }).find { |(a, b)| s88_a(a); s88_b(b); false }
  # hash find |(a, b), c|
  def f89 = ({ "b" => 1, "c" => 2 }).find { |(a, b), c| s89_a(a); s89_c(c); false }
  # hash find |a, (b, c)|
  def f90 = ({ "b" => 1, "c" => 2 }).find { |a, (b, c)| s90_a(a); s90_c(c); false }
  # hash any? |a|
  def f91 = ({ "b" => 1, "c" => 2 }).any? { |a| s91_a(a); false }
  # hash any? |a, b|
  def f92 = ({ "b" => 1, "c" => 2 }).any? { |a, b| s92_a(a); s92_b(b); false }
  # hash any? |a, |
  def f93 = ({ "b" => 1, "c" => 2 }).any? { |a, | s93_a(a); false }
  # hash any? |a, *r|
  def f94 = ({ "b" => 1, "c" => 2 }).any? { |a, *r| s94_a(a); false }
  # hash any? |(a, b)|
  def f95 = ({ "b" => 1, "c" => 2 }).any? { |(a, b)| s95_a(a); s95_b(b); false }
  # hash any? |(a, b), c|
  def f96 = ({ "b" => 1, "c" => 2 }).any? { |(a, b), c| s96_a(a); s96_c(c); false }
  # hash any? |a, (b, c)|
  def f97 = ({ "b" => 1, "c" => 2 }).any? { |a, (b, c)| s97_a(a); s97_c(c); false }
  # hash partition |a|
  def f98 = ({ "b" => 1, "c" => 2 }).partition { |a| s98_a(a); true }
  # hash partition |a, b|
  def f99 = ({ "b" => 1, "c" => 2 }).partition { |a, b| s99_a(a); s99_b(b); true }
  # hash partition |a, |
  def f100 = ({ "b" => 1, "c" => 2 }).partition { |a, | s100_a(a); true }
  # hash partition |a, *r|
  def f101 = ({ "b" => 1, "c" => 2 }).partition { |a, *r| s101_a(a); true }
  # hash partition |(a, b)|
  def f102 = ({ "b" => 1, "c" => 2 }).partition { |(a, b)| s102_a(a); s102_b(b); true }
  # hash partition |(a, b), c|
  def f103 = ({ "b" => 1, "c" => 2 }).partition { |(a, b), c| s103_a(a); s103_c(c); true }
  # hash partition |a, (b, c)|
  def f104 = ({ "b" => 1, "c" => 2 }).partition { |a, (b, c)| s104_a(a); s104_c(c); true }
  # hash each_slice |a|
  def f105 = ({ "b" => 1, "c" => 2 }).each_slice(2) { |a| s105_a(a); nil }
  # hash each_slice |a, b|
  def f106 = ({ "b" => 1, "c" => 2 }).each_slice(2) { |a, b| s106_a(a); s106_b(b); nil }
  # hash each_slice |a, |
  def f107 = ({ "b" => 1, "c" => 2 }).each_slice(2) { |a, | s107_a(a); nil }
  # hash each_slice |a, *r|
  def f108 = ({ "b" => 1, "c" => 2 }).each_slice(2) { |a, *r| s108_a(a); nil }
  # hash each_slice |(a, b)|
  def f109 = ({ "b" => 1, "c" => 2 }).each_slice(2) { |(a, b)| s109_a(a); s109_b(b); nil }
  # hash each_slice |(a, b), c|
  def f110 = ({ "b" => 1, "c" => 2 }).each_slice(2) { |(a, b), c| s110_a(a); s110_c(c); nil }
  # hash each_slice |a, (b, c)|
  def f111 = ({ "b" => 1, "c" => 2 }).each_slice(2) { |a, (b, c)| s111_a(a); s111_c(c); nil }
  # hash each_cons |a|
  def f112 = ({ "b" => 1, "c" => 2 }).each_cons(2) { |a| s112_a(a); nil }
  # hash each_cons |a, b|
  def f113 = ({ "b" => 1, "c" => 2 }).each_cons(2) { |a, b| s113_a(a); s113_b(b); nil }
  # hash each_cons |a, |
  def f114 = ({ "b" => 1, "c" => 2 }).each_cons(2) { |a, | s114_a(a); nil }
  # hash each_cons |a, *r|
  def f115 = ({ "b" => 1, "c" => 2 }).each_cons(2) { |a, *r| s115_a(a); nil }
  # hash each_cons |(a, b)|
  def f116 = ({ "b" => 1, "c" => 2 }).each_cons(2) { |(a, b)| s116_a(a); s116_b(b); nil }
  # hash each_cons |(a, b), c|
  def f117 = ({ "b" => 1, "c" => 2 }).each_cons(2) { |(a, b), c| s117_a(a); s117_c(c); nil }
  # hash each_cons |a, (b, c)|
  def f118 = ({ "b" => 1, "c" => 2 }).each_cons(2) { |a, (b, c)| s118_a(a); s118_c(c); nil }
  # hash each_with_object |a|
  def f119 = ({ "b" => 1, "c" => 2 }).each_with_object([]) { |a| s119_a(a); nil }
  # hash each_with_object |a, b|
  def f120 = ({ "b" => 1, "c" => 2 }).each_with_object([]) { |a, b| s120_a(a); s120_b(b); nil }
  # hash each_with_object |a, |
  def f121 = ({ "b" => 1, "c" => 2 }).each_with_object([]) { |a, | s121_a(a); nil }
  # hash each_with_object |a, *r|
  def f122 = ({ "b" => 1, "c" => 2 }).each_with_object([]) { |a, *r| s122_a(a); nil }
  # hash each_with_object |(a, b)|
  def f123 = ({ "b" => 1, "c" => 2 }).each_with_object([]) { |(a, b)| s123_a(a); s123_b(b); nil }
  # hash each_with_object |(a, b), c|
  def f124 = ({ "b" => 1, "c" => 2 }).each_with_object([]) { |(a, b), c| s124_a(a); s124_c(c); nil }
  # hash each_with_object |a, (b, c)|
  def f125 = ({ "b" => 1, "c" => 2 }).each_with_object([]) { |a, (b, c)| s125_a(a); s125_c(c); nil }
  # hash inject |a|
  def f126 = ({ "b" => 1, "c" => 2 }).inject(0) { |a| s126_a(a); 0 }
  # hash inject |a, b|
  def f127 = ({ "b" => 1, "c" => 2 }).inject(0) { |a, b| s127_a(a); s127_b(b); 0 }
  # hash inject |a, |
  def f128 = ({ "b" => 1, "c" => 2 }).inject(0) { |a, | s128_a(a); 0 }
  # hash inject |a, *r|
  def f129 = ({ "b" => 1, "c" => 2 }).inject(0) { |a, *r| s129_a(a); 0 }
  # hash inject |(a, b)|
  def f130 = ({ "b" => 1, "c" => 2 }).inject(0) { |(a, b)| s130_a(a); s130_b(b); 0 }
  # hash inject |(a, b), c|
  def f131 = ({ "b" => 1, "c" => 2 }).inject(0) { |(a, b), c| s131_a(a); s131_c(c); 0 }
  # hash inject |a, (b, c)|
  def f132 = ({ "b" => 1, "c" => 2 }).inject(0) { |a, (b, c)| s132_a(a); s132_c(c); 0 }
  # pairs each |a|
  def f133 = ([["b", 1], ["c", 2]]).each { |a| s133_a(a); nil }
  # pairs each |a, b|
  def f134 = ([["b", 1], ["c", 2]]).each { |a, b| s134_a(a); s134_b(b); nil }
  # pairs each |a, |
  def f135 = ([["b", 1], ["c", 2]]).each { |a, | s135_a(a); nil }
  # pairs each |a, *r|
  def f136 = ([["b", 1], ["c", 2]]).each { |a, *r| s136_a(a); nil }
  # pairs each |(a, b)|
  def f137 = ([["b", 1], ["c", 2]]).each { |(a, b)| s137_a(a); s137_b(b); nil }
  # pairs each |(a, b), c|
  def f138 = ([["b", 1], ["c", 2]]).each { |(a, b), c| s138_a(a); s138_c(c); nil }
  # pairs each |a, (b, c)|
  def f139 = ([["b", 1], ["c", 2]]).each { |a, (b, c)| s139_a(a); s139_c(c); nil }
  # pairs map |a|
  def f140 = ([["b", 1], ["c", 2]]).map { |a| s140_a(a); nil }
  # pairs map |a, b|
  def f141 = ([["b", 1], ["c", 2]]).map { |a, b| s141_a(a); s141_b(b); nil }
  # pairs map |a, |
  def f142 = ([["b", 1], ["c", 2]]).map { |a, | s142_a(a); nil }
  # pairs map |a, *r|
  def f143 = ([["b", 1], ["c", 2]]).map { |a, *r| s143_a(a); nil }
  # pairs map |(a, b)|
  def f144 = ([["b", 1], ["c", 2]]).map { |(a, b)| s144_a(a); s144_b(b); nil }
  # pairs map |(a, b), c|
  def f145 = ([["b", 1], ["c", 2]]).map { |(a, b), c| s145_a(a); s145_c(c); nil }
  # pairs map |a, (b, c)|
  def f146 = ([["b", 1], ["c", 2]]).map { |a, (b, c)| s146_a(a); s146_c(c); nil }
  # pairs select |a|
  def f147 = ([["b", 1], ["c", 2]]).select { |a| s147_a(a); true }
  # pairs select |a, b|
  def f148 = ([["b", 1], ["c", 2]]).select { |a, b| s148_a(a); s148_b(b); true }
  # pairs select |a, |
  def f149 = ([["b", 1], ["c", 2]]).select { |a, | s149_a(a); true }
  # pairs select |a, *r|
  def f150 = ([["b", 1], ["c", 2]]).select { |a, *r| s150_a(a); true }
  # pairs select |(a, b)|
  def f151 = ([["b", 1], ["c", 2]]).select { |(a, b)| s151_a(a); s151_b(b); true }
  # pairs select |(a, b), c|
  def f152 = ([["b", 1], ["c", 2]]).select { |(a, b), c| s152_a(a); s152_c(c); true }
  # pairs select |a, (b, c)|
  def f153 = ([["b", 1], ["c", 2]]).select { |a, (b, c)| s153_a(a); s153_c(c); true }
  # pairs reject |a|
  def f154 = ([["b", 1], ["c", 2]]).reject { |a| s154_a(a); false }
  # pairs reject |a, b|
  def f155 = ([["b", 1], ["c", 2]]).reject { |a, b| s155_a(a); s155_b(b); false }
  # pairs reject |a, |
  def f156 = ([["b", 1], ["c", 2]]).reject { |a, | s156_a(a); false }
  # pairs reject |a, *r|
  def f157 = ([["b", 1], ["c", 2]]).reject { |a, *r| s157_a(a); false }
  # pairs reject |(a, b)|
  def f158 = ([["b", 1], ["c", 2]]).reject { |(a, b)| s158_a(a); s158_b(b); false }
  # pairs reject |(a, b), c|
  def f159 = ([["b", 1], ["c", 2]]).reject { |(a, b), c| s159_a(a); s159_c(c); false }
  # pairs reject |a, (b, c)|
  def f160 = ([["b", 1], ["c", 2]]).reject { |a, (b, c)| s160_a(a); s160_c(c); false }
  # pairs each_with_index |a|
  def f161 = ([["b", 1], ["c", 2]]).each_with_index { |a| s161_a(a); nil }
  # pairs each_with_index |a, b|
  def f162 = ([["b", 1], ["c", 2]]).each_with_index { |a, b| s162_a(a); s162_b(b); nil }
  # pairs each_with_index |a, |
  def f163 = ([["b", 1], ["c", 2]]).each_with_index { |a, | s163_a(a); nil }
  # pairs each_with_index |a, *r|
  def f164 = ([["b", 1], ["c", 2]]).each_with_index { |a, *r| s164_a(a); nil }
  # pairs each_with_index |(a, b)|
  def f165 = ([["b", 1], ["c", 2]]).each_with_index { |(a, b)| s165_a(a); s165_b(b); nil }
  # pairs each_with_index |(a, b), c|
  def f166 = ([["b", 1], ["c", 2]]).each_with_index { |(a, b), c| s166_a(a); s166_c(c); nil }
  # pairs each_with_index |a, (b, c)|
  def f167 = ([["b", 1], ["c", 2]]).each_with_index { |a, (b, c)| s167_a(a); s167_c(c); nil }
  # pairs sort_by |a|
  def f168 = ([["b", 1], ["c", 2]]).sort_by { |a| s168_a(a); 0 }
  # pairs sort_by |a, b|
  def f169 = ([["b", 1], ["c", 2]]).sort_by { |a, b| s169_a(a); s169_b(b); 0 }
  # pairs sort_by |a, |
  def f170 = ([["b", 1], ["c", 2]]).sort_by { |a, | s170_a(a); 0 }
  # pairs sort_by |a, *r|
  def f171 = ([["b", 1], ["c", 2]]).sort_by { |a, *r| s171_a(a); 0 }
  # pairs sort_by |(a, b)|
  def f172 = ([["b", 1], ["c", 2]]).sort_by { |(a, b)| s172_a(a); s172_b(b); 0 }
  # pairs sort_by |(a, b), c|
  def f173 = ([["b", 1], ["c", 2]]).sort_by { |(a, b), c| s173_a(a); s173_c(c); 0 }
  # pairs sort_by |a, (b, c)|
  def f174 = ([["b", 1], ["c", 2]]).sort_by { |a, (b, c)| s174_a(a); s174_c(c); 0 }
  # pairs min_by |a|
  def f175 = ([["b", 1], ["c", 2]]).min_by { |a| s175_a(a); 0 }
  # pairs min_by |a, b|
  def f176 = ([["b", 1], ["c", 2]]).min_by { |a, b| s176_a(a); s176_b(b); 0 }
  # pairs min_by |a, |
  def f177 = ([["b", 1], ["c", 2]]).min_by { |a, | s177_a(a); 0 }
  # pairs min_by |a, *r|
  def f178 = ([["b", 1], ["c", 2]]).min_by { |a, *r| s178_a(a); 0 }
  # pairs min_by |(a, b)|
  def f179 = ([["b", 1], ["c", 2]]).min_by { |(a, b)| s179_a(a); s179_b(b); 0 }
  # pairs min_by |(a, b), c|
  def f180 = ([["b", 1], ["c", 2]]).min_by { |(a, b), c| s180_a(a); s180_c(c); 0 }
  # pairs min_by |a, (b, c)|
  def f181 = ([["b", 1], ["c", 2]]).min_by { |a, (b, c)| s181_a(a); s181_c(c); 0 }
  # pairs group_by |a|
  def f182 = ([["b", 1], ["c", 2]]).group_by { |a| s182_a(a); 0 }
  # pairs group_by |a, b|
  def f183 = ([["b", 1], ["c", 2]]).group_by { |a, b| s183_a(a); s183_b(b); 0 }
  # pairs group_by |a, |
  def f184 = ([["b", 1], ["c", 2]]).group_by { |a, | s184_a(a); 0 }
  # pairs group_by |a, *r|
  def f185 = ([["b", 1], ["c", 2]]).group_by { |a, *r| s185_a(a); 0 }
  # pairs group_by |(a, b)|
  def f186 = ([["b", 1], ["c", 2]]).group_by { |(a, b)| s186_a(a); s186_b(b); 0 }
  # pairs group_by |(a, b), c|
  def f187 = ([["b", 1], ["c", 2]]).group_by { |(a, b), c| s187_a(a); s187_c(c); 0 }
  # pairs group_by |a, (b, c)|
  def f188 = ([["b", 1], ["c", 2]]).group_by { |a, (b, c)| s188_a(a); s188_c(c); 0 }
  # pairs sum |a|
  def f189 = ([["b", 1], ["c", 2]]).sum { |a| s189_a(a); 0 }
  # pairs sum |a, b|
  def f190 = ([["b", 1], ["c", 2]]).sum { |a, b| s190_a(a); s190_b(b); 0 }
  # pairs sum |a, |
  def f191 = ([["b", 1], ["c", 2]]).sum { |a, | s191_a(a); 0 }
  # pairs sum |a, *r|
  def f192 = ([["b", 1], ["c", 2]]).sum { |a, *r| s192_a(a); 0 }
  # pairs sum |(a, b)|
  def f193 = ([["b", 1], ["c", 2]]).sum { |(a, b)| s193_a(a); s193_b(b); 0 }
  # pairs sum |(a, b), c|
  def f194 = ([["b", 1], ["c", 2]]).sum { |(a, b), c| s194_a(a); s194_c(c); 0 }
  # pairs sum |a, (b, c)|
  def f195 = ([["b", 1], ["c", 2]]).sum { |a, (b, c)| s195_a(a); s195_c(c); 0 }
  # pairs filter_map |a|
  def f196 = ([["b", 1], ["c", 2]]).filter_map { |a| s196_a(a); nil }
  # pairs filter_map |a, b|
  def f197 = ([["b", 1], ["c", 2]]).filter_map { |a, b| s197_a(a); s197_b(b); nil }
  # pairs filter_map |a, |
  def f198 = ([["b", 1], ["c", 2]]).filter_map { |a, | s198_a(a); nil }
  # pairs filter_map |a, *r|
  def f199 = ([["b", 1], ["c", 2]]).filter_map { |a, *r| s199_a(a); nil }
  # pairs filter_map |(a, b)|
  def f200 = ([["b", 1], ["c", 2]]).filter_map { |(a, b)| s200_a(a); s200_b(b); nil }
  # pairs filter_map |(a, b), c|
  def f201 = ([["b", 1], ["c", 2]]).filter_map { |(a, b), c| s201_a(a); s201_c(c); nil }
  # pairs filter_map |a, (b, c)|
  def f202 = ([["b", 1], ["c", 2]]).filter_map { |a, (b, c)| s202_a(a); s202_c(c); nil }
  # pairs flat_map |a|
  def f203 = ([["b", 1], ["c", 2]]).flat_map { |a| s203_a(a); [] }
  # pairs flat_map |a, b|
  def f204 = ([["b", 1], ["c", 2]]).flat_map { |a, b| s204_a(a); s204_b(b); [] }
  # pairs flat_map |a, |
  def f205 = ([["b", 1], ["c", 2]]).flat_map { |a, | s205_a(a); [] }
  # pairs flat_map |a, *r|
  def f206 = ([["b", 1], ["c", 2]]).flat_map { |a, *r| s206_a(a); [] }
  # pairs flat_map |(a, b)|
  def f207 = ([["b", 1], ["c", 2]]).flat_map { |(a, b)| s207_a(a); s207_b(b); [] }
  # pairs flat_map |(a, b), c|
  def f208 = ([["b", 1], ["c", 2]]).flat_map { |(a, b), c| s208_a(a); s208_c(c); [] }
  # pairs flat_map |a, (b, c)|
  def f209 = ([["b", 1], ["c", 2]]).flat_map { |a, (b, c)| s209_a(a); s209_c(c); [] }
  # pairs count |a|
  def f210 = ([["b", 1], ["c", 2]]).count { |a| s210_a(a); true }
  # pairs count |a, b|
  def f211 = ([["b", 1], ["c", 2]]).count { |a, b| s211_a(a); s211_b(b); true }
  # pairs count |a, |
  def f212 = ([["b", 1], ["c", 2]]).count { |a, | s212_a(a); true }
  # pairs count |a, *r|
  def f213 = ([["b", 1], ["c", 2]]).count { |a, *r| s213_a(a); true }
  # pairs count |(a, b)|
  def f214 = ([["b", 1], ["c", 2]]).count { |(a, b)| s214_a(a); s214_b(b); true }
  # pairs count |(a, b), c|
  def f215 = ([["b", 1], ["c", 2]]).count { |(a, b), c| s215_a(a); s215_c(c); true }
  # pairs count |a, (b, c)|
  def f216 = ([["b", 1], ["c", 2]]).count { |a, (b, c)| s216_a(a); s216_c(c); true }
  # pairs find |a|
  def f217 = ([["b", 1], ["c", 2]]).find { |a| s217_a(a); false }
  # pairs find |a, b|
  def f218 = ([["b", 1], ["c", 2]]).find { |a, b| s218_a(a); s218_b(b); false }
  # pairs find |a, |
  def f219 = ([["b", 1], ["c", 2]]).find { |a, | s219_a(a); false }
  # pairs find |a, *r|
  def f220 = ([["b", 1], ["c", 2]]).find { |a, *r| s220_a(a); false }
  # pairs find |(a, b)|
  def f221 = ([["b", 1], ["c", 2]]).find { |(a, b)| s221_a(a); s221_b(b); false }
  # pairs find |(a, b), c|
  def f222 = ([["b", 1], ["c", 2]]).find { |(a, b), c| s222_a(a); s222_c(c); false }
  # pairs find |a, (b, c)|
  def f223 = ([["b", 1], ["c", 2]]).find { |a, (b, c)| s223_a(a); s223_c(c); false }
  # pairs any? |a|
  def f224 = ([["b", 1], ["c", 2]]).any? { |a| s224_a(a); false }
  # pairs any? |a, b|
  def f225 = ([["b", 1], ["c", 2]]).any? { |a, b| s225_a(a); s225_b(b); false }
  # pairs any? |a, |
  def f226 = ([["b", 1], ["c", 2]]).any? { |a, | s226_a(a); false }
  # pairs any? |a, *r|
  def f227 = ([["b", 1], ["c", 2]]).any? { |a, *r| s227_a(a); false }
  # pairs any? |(a, b)|
  def f228 = ([["b", 1], ["c", 2]]).any? { |(a, b)| s228_a(a); s228_b(b); false }
  # pairs any? |(a, b), c|
  def f229 = ([["b", 1], ["c", 2]]).any? { |(a, b), c| s229_a(a); s229_c(c); false }
  # pairs any? |a, (b, c)|
  def f230 = ([["b", 1], ["c", 2]]).any? { |a, (b, c)| s230_a(a); s230_c(c); false }
  # pairs partition |a|
  def f231 = ([["b", 1], ["c", 2]]).partition { |a| s231_a(a); true }
  # pairs partition |a, b|
  def f232 = ([["b", 1], ["c", 2]]).partition { |a, b| s232_a(a); s232_b(b); true }
  # pairs partition |a, |
  def f233 = ([["b", 1], ["c", 2]]).partition { |a, | s233_a(a); true }
  # pairs partition |a, *r|
  def f234 = ([["b", 1], ["c", 2]]).partition { |a, *r| s234_a(a); true }
  # pairs partition |(a, b)|
  def f235 = ([["b", 1], ["c", 2]]).partition { |(a, b)| s235_a(a); s235_b(b); true }
  # pairs partition |(a, b), c|
  def f236 = ([["b", 1], ["c", 2]]).partition { |(a, b), c| s236_a(a); s236_c(c); true }
  # pairs partition |a, (b, c)|
  def f237 = ([["b", 1], ["c", 2]]).partition { |a, (b, c)| s237_a(a); s237_c(c); true }
  # pairs each_slice |a|
  def f238 = ([["b", 1], ["c", 2]]).each_slice(2) { |a| s238_a(a); nil }
  # pairs each_slice |a, b|
  def f239 = ([["b", 1], ["c", 2]]).each_slice(2) { |a, b| s239_a(a); s239_b(b); nil }
  # pairs each_slice |a, |
  def f240 = ([["b", 1], ["c", 2]]).each_slice(2) { |a, | s240_a(a); nil }
  # pairs each_slice |a, *r|
  def f241 = ([["b", 1], ["c", 2]]).each_slice(2) { |a, *r| s241_a(a); nil }
  # pairs each_slice |(a, b)|
  def f242 = ([["b", 1], ["c", 2]]).each_slice(2) { |(a, b)| s242_a(a); s242_b(b); nil }
  # pairs each_slice |(a, b), c|
  def f243 = ([["b", 1], ["c", 2]]).each_slice(2) { |(a, b), c| s243_a(a); s243_c(c); nil }
  # pairs each_slice |a, (b, c)|
  def f244 = ([["b", 1], ["c", 2]]).each_slice(2) { |a, (b, c)| s244_a(a); s244_c(c); nil }
  # pairs each_cons |a|
  def f245 = ([["b", 1], ["c", 2]]).each_cons(2) { |a| s245_a(a); nil }
  # pairs each_cons |a, b|
  def f246 = ([["b", 1], ["c", 2]]).each_cons(2) { |a, b| s246_a(a); s246_b(b); nil }
  # pairs each_cons |a, |
  def f247 = ([["b", 1], ["c", 2]]).each_cons(2) { |a, | s247_a(a); nil }
  # pairs each_cons |a, *r|
  def f248 = ([["b", 1], ["c", 2]]).each_cons(2) { |a, *r| s248_a(a); nil }
  # pairs each_cons |(a, b)|
  def f249 = ([["b", 1], ["c", 2]]).each_cons(2) { |(a, b)| s249_a(a); s249_b(b); nil }
  # pairs each_cons |(a, b), c|
  def f250 = ([["b", 1], ["c", 2]]).each_cons(2) { |(a, b), c| s250_a(a); s250_c(c); nil }
  # pairs each_cons |a, (b, c)|
  def f251 = ([["b", 1], ["c", 2]]).each_cons(2) { |a, (b, c)| s251_a(a); s251_c(c); nil }
  # pairs each_with_object |a|
  def f252 = ([["b", 1], ["c", 2]]).each_with_object([]) { |a| s252_a(a); nil }
  # pairs each_with_object |a, b|
  def f253 = ([["b", 1], ["c", 2]]).each_with_object([]) { |a, b| s253_a(a); s253_b(b); nil }
  # pairs each_with_object |a, |
  def f254 = ([["b", 1], ["c", 2]]).each_with_object([]) { |a, | s254_a(a); nil }
  # pairs each_with_object |a, *r|
  def f255 = ([["b", 1], ["c", 2]]).each_with_object([]) { |a, *r| s255_a(a); nil }
  # pairs each_with_object |(a, b)|
  def f256 = ([["b", 1], ["c", 2]]).each_with_object([]) { |(a, b)| s256_a(a); s256_b(b); nil }
  # pairs each_with_object |(a, b), c|
  def f257 = ([["b", 1], ["c", 2]]).each_with_object([]) { |(a, b), c| s257_a(a); s257_c(c); nil }
  # pairs each_with_object |a, (b, c)|
  def f258 = ([["b", 1], ["c", 2]]).each_with_object([]) { |a, (b, c)| s258_a(a); s258_c(c); nil }
  # pairs inject |a|
  def f259 = ([["b", 1], ["c", 2]]).inject(0) { |a| s259_a(a); 0 }
  # pairs inject |a, b|
  def f260 = ([["b", 1], ["c", 2]]).inject(0) { |a, b| s260_a(a); s260_b(b); 0 }
  # pairs inject |a, |
  def f261 = ([["b", 1], ["c", 2]]).inject(0) { |a, | s261_a(a); 0 }
  # pairs inject |a, *r|
  def f262 = ([["b", 1], ["c", 2]]).inject(0) { |a, *r| s262_a(a); 0 }
  # pairs inject |(a, b)|
  def f263 = ([["b", 1], ["c", 2]]).inject(0) { |(a, b)| s263_a(a); s263_b(b); 0 }
  # pairs inject |(a, b), c|
  def f264 = ([["b", 1], ["c", 2]]).inject(0) { |(a, b), c| s264_a(a); s264_c(c); 0 }
  # pairs inject |a, (b, c)|
  def f265 = ([["b", 1], ["c", 2]]).inject(0) { |a, (b, c)| s265_a(a); s265_c(c); 0 }
  # ragged each |a|
  def f266 = ("1:2,3".split(",").map { |s| s.split(":") }).each { |a| s266_a(a); nil }
  # ragged each |a, b|
  def f267 = ("1:2,3".split(",").map { |s| s.split(":") }).each { |a, b| s267_a(a); s267_b(b); nil }
  # ragged each |a, |
  def f268 = ("1:2,3".split(",").map { |s| s.split(":") }).each { |a, | s268_a(a); nil }
  # ragged each |a, *r|
  def f269 = ("1:2,3".split(",").map { |s| s.split(":") }).each { |a, *r| s269_a(a); nil }
  # ragged each |(a, b)|
  def f270 = ("1:2,3".split(",").map { |s| s.split(":") }).each { |(a, b)| s270_a(a); s270_b(b); nil }
  # ragged each |(a, b), c|
  def f271 = ("1:2,3".split(",").map { |s| s.split(":") }).each { |(a, b), c| s271_a(a); s271_c(c); nil }
  # ragged each |a, (b, c)|
  def f272 = ("1:2,3".split(",").map { |s| s.split(":") }).each { |a, (b, c)| s272_a(a); s272_c(c); nil }
  # ragged map |a|
  def f273 = ("1:2,3".split(",").map { |s| s.split(":") }).map { |a| s273_a(a); nil }
  # ragged map |a, b|
  def f274 = ("1:2,3".split(",").map { |s| s.split(":") }).map { |a, b| s274_a(a); s274_b(b); nil }
  # ragged map |a, |
  def f275 = ("1:2,3".split(",").map { |s| s.split(":") }).map { |a, | s275_a(a); nil }
  # ragged map |a, *r|
  def f276 = ("1:2,3".split(",").map { |s| s.split(":") }).map { |a, *r| s276_a(a); nil }
  # ragged map |(a, b)|
  def f277 = ("1:2,3".split(",").map { |s| s.split(":") }).map { |(a, b)| s277_a(a); s277_b(b); nil }
  # ragged map |(a, b), c|
  def f278 = ("1:2,3".split(",").map { |s| s.split(":") }).map { |(a, b), c| s278_a(a); s278_c(c); nil }
  # ragged map |a, (b, c)|
  def f279 = ("1:2,3".split(",").map { |s| s.split(":") }).map { |a, (b, c)| s279_a(a); s279_c(c); nil }
  # ragged select |a|
  def f280 = ("1:2,3".split(",").map { |s| s.split(":") }).select { |a| s280_a(a); true }
  # ragged select |a, b|
  def f281 = ("1:2,3".split(",").map { |s| s.split(":") }).select { |a, b| s281_a(a); s281_b(b); true }
  # ragged select |a, |
  def f282 = ("1:2,3".split(",").map { |s| s.split(":") }).select { |a, | s282_a(a); true }
  # ragged select |a, *r|
  def f283 = ("1:2,3".split(",").map { |s| s.split(":") }).select { |a, *r| s283_a(a); true }
  # ragged select |(a, b)|
  def f284 = ("1:2,3".split(",").map { |s| s.split(":") }).select { |(a, b)| s284_a(a); s284_b(b); true }
  # ragged select |(a, b), c|
  def f285 = ("1:2,3".split(",").map { |s| s.split(":") }).select { |(a, b), c| s285_a(a); s285_c(c); true }
  # ragged select |a, (b, c)|
  def f286 = ("1:2,3".split(",").map { |s| s.split(":") }).select { |a, (b, c)| s286_a(a); s286_c(c); true }
  # ragged reject |a|
  def f287 = ("1:2,3".split(",").map { |s| s.split(":") }).reject { |a| s287_a(a); false }
  # ragged reject |a, b|
  def f288 = ("1:2,3".split(",").map { |s| s.split(":") }).reject { |a, b| s288_a(a); s288_b(b); false }
  # ragged reject |a, |
  def f289 = ("1:2,3".split(",").map { |s| s.split(":") }).reject { |a, | s289_a(a); false }
  # ragged reject |a, *r|
  def f290 = ("1:2,3".split(",").map { |s| s.split(":") }).reject { |a, *r| s290_a(a); false }
  # ragged reject |(a, b)|
  def f291 = ("1:2,3".split(",").map { |s| s.split(":") }).reject { |(a, b)| s291_a(a); s291_b(b); false }
  # ragged reject |(a, b), c|
  def f292 = ("1:2,3".split(",").map { |s| s.split(":") }).reject { |(a, b), c| s292_a(a); s292_c(c); false }
  # ragged reject |a, (b, c)|
  def f293 = ("1:2,3".split(",").map { |s| s.split(":") }).reject { |a, (b, c)| s293_a(a); s293_c(c); false }
  # ragged each_with_index |a|
  def f294 = ("1:2,3".split(",").map { |s| s.split(":") }).each_with_index { |a| s294_a(a); nil }
  # ragged each_with_index |a, b|
  def f295 = ("1:2,3".split(",").map { |s| s.split(":") }).each_with_index { |a, b| s295_a(a); s295_b(b); nil }
  # ragged each_with_index |a, |
  def f296 = ("1:2,3".split(",").map { |s| s.split(":") }).each_with_index { |a, | s296_a(a); nil }
  # ragged each_with_index |a, *r|
  def f297 = ("1:2,3".split(",").map { |s| s.split(":") }).each_with_index { |a, *r| s297_a(a); nil }
  # ragged each_with_index |(a, b)|
  def f298 = ("1:2,3".split(",").map { |s| s.split(":") }).each_with_index { |(a, b)| s298_a(a); s298_b(b); nil }
  # ragged each_with_index |(a, b), c|
  def f299 = ("1:2,3".split(",").map { |s| s.split(":") }).each_with_index { |(a, b), c| s299_a(a); s299_c(c); nil }
  # ragged each_with_index |a, (b, c)|
  def f300 = ("1:2,3".split(",").map { |s| s.split(":") }).each_with_index { |a, (b, c)| s300_a(a); s300_c(c); nil }
  # ragged sort_by |a|
  def f301 = ("1:2,3".split(",").map { |s| s.split(":") }).sort_by { |a| s301_a(a); 0 }
  # ragged sort_by |a, b|
  def f302 = ("1:2,3".split(",").map { |s| s.split(":") }).sort_by { |a, b| s302_a(a); s302_b(b); 0 }
  # ragged sort_by |a, |
  def f303 = ("1:2,3".split(",").map { |s| s.split(":") }).sort_by { |a, | s303_a(a); 0 }
  # ragged sort_by |a, *r|
  def f304 = ("1:2,3".split(",").map { |s| s.split(":") }).sort_by { |a, *r| s304_a(a); 0 }
  # ragged sort_by |(a, b)|
  def f305 = ("1:2,3".split(",").map { |s| s.split(":") }).sort_by { |(a, b)| s305_a(a); s305_b(b); 0 }
  # ragged sort_by |(a, b), c|
  def f306 = ("1:2,3".split(",").map { |s| s.split(":") }).sort_by { |(a, b), c| s306_a(a); s306_c(c); 0 }
  # ragged sort_by |a, (b, c)|
  def f307 = ("1:2,3".split(",").map { |s| s.split(":") }).sort_by { |a, (b, c)| s307_a(a); s307_c(c); 0 }
  # ragged min_by |a|
  def f308 = ("1:2,3".split(",").map { |s| s.split(":") }).min_by { |a| s308_a(a); 0 }
  # ragged min_by |a, b|
  def f309 = ("1:2,3".split(",").map { |s| s.split(":") }).min_by { |a, b| s309_a(a); s309_b(b); 0 }
  # ragged min_by |a, |
  def f310 = ("1:2,3".split(",").map { |s| s.split(":") }).min_by { |a, | s310_a(a); 0 }
  # ragged min_by |a, *r|
  def f311 = ("1:2,3".split(",").map { |s| s.split(":") }).min_by { |a, *r| s311_a(a); 0 }
  # ragged min_by |(a, b)|
  def f312 = ("1:2,3".split(",").map { |s| s.split(":") }).min_by { |(a, b)| s312_a(a); s312_b(b); 0 }
  # ragged min_by |(a, b), c|
  def f313 = ("1:2,3".split(",").map { |s| s.split(":") }).min_by { |(a, b), c| s313_a(a); s313_c(c); 0 }
  # ragged min_by |a, (b, c)|
  def f314 = ("1:2,3".split(",").map { |s| s.split(":") }).min_by { |a, (b, c)| s314_a(a); s314_c(c); 0 }
  # ragged group_by |a|
  def f315 = ("1:2,3".split(",").map { |s| s.split(":") }).group_by { |a| s315_a(a); 0 }
  # ragged group_by |a, b|
  def f316 = ("1:2,3".split(",").map { |s| s.split(":") }).group_by { |a, b| s316_a(a); s316_b(b); 0 }
  # ragged group_by |a, |
  def f317 = ("1:2,3".split(",").map { |s| s.split(":") }).group_by { |a, | s317_a(a); 0 }
  # ragged group_by |a, *r|
  def f318 = ("1:2,3".split(",").map { |s| s.split(":") }).group_by { |a, *r| s318_a(a); 0 }
  # ragged group_by |(a, b)|
  def f319 = ("1:2,3".split(",").map { |s| s.split(":") }).group_by { |(a, b)| s319_a(a); s319_b(b); 0 }
  # ragged group_by |(a, b), c|
  def f320 = ("1:2,3".split(",").map { |s| s.split(":") }).group_by { |(a, b), c| s320_a(a); s320_c(c); 0 }
  # ragged group_by |a, (b, c)|
  def f321 = ("1:2,3".split(",").map { |s| s.split(":") }).group_by { |a, (b, c)| s321_a(a); s321_c(c); 0 }
  # ragged sum |a|
  def f322 = ("1:2,3".split(",").map { |s| s.split(":") }).sum { |a| s322_a(a); 0 }
  # ragged sum |a, b|
  def f323 = ("1:2,3".split(",").map { |s| s.split(":") }).sum { |a, b| s323_a(a); s323_b(b); 0 }
  # ragged sum |a, |
  def f324 = ("1:2,3".split(",").map { |s| s.split(":") }).sum { |a, | s324_a(a); 0 }
  # ragged sum |a, *r|
  def f325 = ("1:2,3".split(",").map { |s| s.split(":") }).sum { |a, *r| s325_a(a); 0 }
  # ragged sum |(a, b)|
  def f326 = ("1:2,3".split(",").map { |s| s.split(":") }).sum { |(a, b)| s326_a(a); s326_b(b); 0 }
  # ragged sum |(a, b), c|
  def f327 = ("1:2,3".split(",").map { |s| s.split(":") }).sum { |(a, b), c| s327_a(a); s327_c(c); 0 }
  # ragged sum |a, (b, c)|
  def f328 = ("1:2,3".split(",").map { |s| s.split(":") }).sum { |a, (b, c)| s328_a(a); s328_c(c); 0 }
  # ragged filter_map |a|
  def f329 = ("1:2,3".split(",").map { |s| s.split(":") }).filter_map { |a| s329_a(a); nil }
  # ragged filter_map |a, b|
  def f330 = ("1:2,3".split(",").map { |s| s.split(":") }).filter_map { |a, b| s330_a(a); s330_b(b); nil }
  # ragged filter_map |a, |
  def f331 = ("1:2,3".split(",").map { |s| s.split(":") }).filter_map { |a, | s331_a(a); nil }
  # ragged filter_map |a, *r|
  def f332 = ("1:2,3".split(",").map { |s| s.split(":") }).filter_map { |a, *r| s332_a(a); nil }
  # ragged filter_map |(a, b)|
  def f333 = ("1:2,3".split(",").map { |s| s.split(":") }).filter_map { |(a, b)| s333_a(a); s333_b(b); nil }
  # ragged filter_map |(a, b), c|
  def f334 = ("1:2,3".split(",").map { |s| s.split(":") }).filter_map { |(a, b), c| s334_a(a); s334_c(c); nil }
  # ragged filter_map |a, (b, c)|
  def f335 = ("1:2,3".split(",").map { |s| s.split(":") }).filter_map { |a, (b, c)| s335_a(a); s335_c(c); nil }
  # ragged flat_map |a|
  def f336 = ("1:2,3".split(",").map { |s| s.split(":") }).flat_map { |a| s336_a(a); [] }
  # ragged flat_map |a, b|
  def f337 = ("1:2,3".split(",").map { |s| s.split(":") }).flat_map { |a, b| s337_a(a); s337_b(b); [] }
  # ragged flat_map |a, |
  def f338 = ("1:2,3".split(",").map { |s| s.split(":") }).flat_map { |a, | s338_a(a); [] }
  # ragged flat_map |a, *r|
  def f339 = ("1:2,3".split(",").map { |s| s.split(":") }).flat_map { |a, *r| s339_a(a); [] }
  # ragged flat_map |(a, b)|
  def f340 = ("1:2,3".split(",").map { |s| s.split(":") }).flat_map { |(a, b)| s340_a(a); s340_b(b); [] }
  # ragged flat_map |(a, b), c|
  def f341 = ("1:2,3".split(",").map { |s| s.split(":") }).flat_map { |(a, b), c| s341_a(a); s341_c(c); [] }
  # ragged flat_map |a, (b, c)|
  def f342 = ("1:2,3".split(",").map { |s| s.split(":") }).flat_map { |a, (b, c)| s342_a(a); s342_c(c); [] }
  # ragged count |a|
  def f343 = ("1:2,3".split(",").map { |s| s.split(":") }).count { |a| s343_a(a); true }
  # ragged count |a, b|
  def f344 = ("1:2,3".split(",").map { |s| s.split(":") }).count { |a, b| s344_a(a); s344_b(b); true }
  # ragged count |a, |
  def f345 = ("1:2,3".split(",").map { |s| s.split(":") }).count { |a, | s345_a(a); true }
  # ragged count |a, *r|
  def f346 = ("1:2,3".split(",").map { |s| s.split(":") }).count { |a, *r| s346_a(a); true }
  # ragged count |(a, b)|
  def f347 = ("1:2,3".split(",").map { |s| s.split(":") }).count { |(a, b)| s347_a(a); s347_b(b); true }
  # ragged count |(a, b), c|
  def f348 = ("1:2,3".split(",").map { |s| s.split(":") }).count { |(a, b), c| s348_a(a); s348_c(c); true }
  # ragged count |a, (b, c)|
  def f349 = ("1:2,3".split(",").map { |s| s.split(":") }).count { |a, (b, c)| s349_a(a); s349_c(c); true }
  # ragged find |a|
  def f350 = ("1:2,3".split(",").map { |s| s.split(":") }).find { |a| s350_a(a); false }
  # ragged find |a, b|
  def f351 = ("1:2,3".split(",").map { |s| s.split(":") }).find { |a, b| s351_a(a); s351_b(b); false }
  # ragged find |a, |
  def f352 = ("1:2,3".split(",").map { |s| s.split(":") }).find { |a, | s352_a(a); false }
  # ragged find |a, *r|
  def f353 = ("1:2,3".split(",").map { |s| s.split(":") }).find { |a, *r| s353_a(a); false }
  # ragged find |(a, b)|
  def f354 = ("1:2,3".split(",").map { |s| s.split(":") }).find { |(a, b)| s354_a(a); s354_b(b); false }
  # ragged find |(a, b), c|
  def f355 = ("1:2,3".split(",").map { |s| s.split(":") }).find { |(a, b), c| s355_a(a); s355_c(c); false }
  # ragged find |a, (b, c)|
  def f356 = ("1:2,3".split(",").map { |s| s.split(":") }).find { |a, (b, c)| s356_a(a); s356_c(c); false }
  # ragged any? |a|
  def f357 = ("1:2,3".split(",").map { |s| s.split(":") }).any? { |a| s357_a(a); false }
  # ragged any? |a, b|
  def f358 = ("1:2,3".split(",").map { |s| s.split(":") }).any? { |a, b| s358_a(a); s358_b(b); false }
  # ragged any? |a, |
  def f359 = ("1:2,3".split(",").map { |s| s.split(":") }).any? { |a, | s359_a(a); false }
  # ragged any? |a, *r|
  def f360 = ("1:2,3".split(",").map { |s| s.split(":") }).any? { |a, *r| s360_a(a); false }
  # ragged any? |(a, b)|
  def f361 = ("1:2,3".split(",").map { |s| s.split(":") }).any? { |(a, b)| s361_a(a); s361_b(b); false }
  # ragged any? |(a, b), c|
  def f362 = ("1:2,3".split(",").map { |s| s.split(":") }).any? { |(a, b), c| s362_a(a); s362_c(c); false }
  # ragged any? |a, (b, c)|
  def f363 = ("1:2,3".split(",").map { |s| s.split(":") }).any? { |a, (b, c)| s363_a(a); s363_c(c); false }
  # ragged partition |a|
  def f364 = ("1:2,3".split(",").map { |s| s.split(":") }).partition { |a| s364_a(a); true }
  # ragged partition |a, b|
  def f365 = ("1:2,3".split(",").map { |s| s.split(":") }).partition { |a, b| s365_a(a); s365_b(b); true }
  # ragged partition |a, |
  def f366 = ("1:2,3".split(",").map { |s| s.split(":") }).partition { |a, | s366_a(a); true }
  # ragged partition |a, *r|
  def f367 = ("1:2,3".split(",").map { |s| s.split(":") }).partition { |a, *r| s367_a(a); true }
  # ragged partition |(a, b)|
  def f368 = ("1:2,3".split(",").map { |s| s.split(":") }).partition { |(a, b)| s368_a(a); s368_b(b); true }
  # ragged partition |(a, b), c|
  def f369 = ("1:2,3".split(",").map { |s| s.split(":") }).partition { |(a, b), c| s369_a(a); s369_c(c); true }
  # ragged partition |a, (b, c)|
  def f370 = ("1:2,3".split(",").map { |s| s.split(":") }).partition { |a, (b, c)| s370_a(a); s370_c(c); true }
  # ragged each_slice |a|
  def f371 = ("1:2,3".split(",").map { |s| s.split(":") }).each_slice(2) { |a| s371_a(a); nil }
  # ragged each_slice |a, b|
  def f372 = ("1:2,3".split(",").map { |s| s.split(":") }).each_slice(2) { |a, b| s372_a(a); s372_b(b); nil }
  # ragged each_slice |a, |
  def f373 = ("1:2,3".split(",").map { |s| s.split(":") }).each_slice(2) { |a, | s373_a(a); nil }
  # ragged each_slice |a, *r|
  def f374 = ("1:2,3".split(",").map { |s| s.split(":") }).each_slice(2) { |a, *r| s374_a(a); nil }
  # ragged each_slice |(a, b)|
  def f375 = ("1:2,3".split(",").map { |s| s.split(":") }).each_slice(2) { |(a, b)| s375_a(a); s375_b(b); nil }
  # ragged each_slice |(a, b), c|
  def f376 = ("1:2,3".split(",").map { |s| s.split(":") }).each_slice(2) { |(a, b), c| s376_a(a); s376_c(c); nil }
  # ragged each_slice |a, (b, c)|
  def f377 = ("1:2,3".split(",").map { |s| s.split(":") }).each_slice(2) { |a, (b, c)| s377_a(a); s377_c(c); nil }
  # ragged each_cons |a|
  def f378 = ("1:2,3".split(",").map { |s| s.split(":") }).each_cons(2) { |a| s378_a(a); nil }
  # ragged each_cons |a, b|
  def f379 = ("1:2,3".split(",").map { |s| s.split(":") }).each_cons(2) { |a, b| s379_a(a); s379_b(b); nil }
  # ragged each_cons |a, |
  def f380 = ("1:2,3".split(",").map { |s| s.split(":") }).each_cons(2) { |a, | s380_a(a); nil }
  # ragged each_cons |a, *r|
  def f381 = ("1:2,3".split(",").map { |s| s.split(":") }).each_cons(2) { |a, *r| s381_a(a); nil }
  # ragged each_cons |(a, b)|
  def f382 = ("1:2,3".split(",").map { |s| s.split(":") }).each_cons(2) { |(a, b)| s382_a(a); s382_b(b); nil }
  # ragged each_cons |(a, b), c|
  def f383 = ("1:2,3".split(",").map { |s| s.split(":") }).each_cons(2) { |(a, b), c| s383_a(a); s383_c(c); nil }
  # ragged each_cons |a, (b, c)|
  def f384 = ("1:2,3".split(",").map { |s| s.split(":") }).each_cons(2) { |a, (b, c)| s384_a(a); s384_c(c); nil }
  # ragged each_with_object |a|
  def f385 = ("1:2,3".split(",").map { |s| s.split(":") }).each_with_object([]) { |a| s385_a(a); nil }
  # ragged each_with_object |a, b|
  def f386 = ("1:2,3".split(",").map { |s| s.split(":") }).each_with_object([]) { |a, b| s386_a(a); s386_b(b); nil }
  # ragged each_with_object |a, |
  def f387 = ("1:2,3".split(",").map { |s| s.split(":") }).each_with_object([]) { |a, | s387_a(a); nil }
  # ragged each_with_object |a, *r|
  def f388 = ("1:2,3".split(",").map { |s| s.split(":") }).each_with_object([]) { |a, *r| s388_a(a); nil }
  # ragged each_with_object |(a, b)|
  def f389 = ("1:2,3".split(",").map { |s| s.split(":") }).each_with_object([]) { |(a, b)| s389_a(a); s389_b(b); nil }
  # ragged each_with_object |(a, b), c|
  def f390 = ("1:2,3".split(",").map { |s| s.split(":") }).each_with_object([]) { |(a, b), c| s390_a(a); s390_c(c); nil }
  # ragged each_with_object |a, (b, c)|
  def f391 = ("1:2,3".split(",").map { |s| s.split(":") }).each_with_object([]) { |a, (b, c)| s391_a(a); s391_c(c); nil }
  # ragged inject |a|
  def f392 = ("1:2,3".split(",").map { |s| s.split(":") }).inject(0) { |a| s392_a(a); 0 }
  # ragged inject |a, b|
  def f393 = ("1:2,3".split(",").map { |s| s.split(":") }).inject(0) { |a, b| s393_a(a); s393_b(b); 0 }
  # ragged inject |a, |
  def f394 = ("1:2,3".split(",").map { |s| s.split(":") }).inject(0) { |a, | s394_a(a); 0 }
  # ragged inject |a, *r|
  def f395 = ("1:2,3".split(",").map { |s| s.split(":") }).inject(0) { |a, *r| s395_a(a); 0 }
  # ragged inject |(a, b)|
  def f396 = ("1:2,3".split(",").map { |s| s.split(":") }).inject(0) { |(a, b)| s396_a(a); s396_b(b); 0 }
  # ragged inject |(a, b), c|
  def f397 = ("1:2,3".split(",").map { |s| s.split(":") }).inject(0) { |(a, b), c| s397_a(a); s397_c(c); 0 }
  # ragged inject |a, (b, c)|
  def f398 = ("1:2,3".split(",").map { |s| s.split(":") }).inject(0) { |a, (b, c)| s398_a(a); s398_c(c); 0 }
  # ints each |a|
  def f399 = ([1, 2, 3]).each { |a| s399_a(a); nil }
  # ints each |a, b|
  def f400 = ([1, 2, 3]).each { |a, b| s400_a(a); s400_b(b); nil }
  # ints each |a, |
  def f401 = ([1, 2, 3]).each { |a, | s401_a(a); nil }
  # ints each |a, *r|
  def f402 = ([1, 2, 3]).each { |a, *r| s402_a(a); nil }
  # ints each |(a, b)|
  def f403 = ([1, 2, 3]).each { |(a, b)| s403_a(a); s403_b(b); nil }
  # ints each |(a, b), c|
  def f404 = ([1, 2, 3]).each { |(a, b), c| s404_a(a); s404_c(c); nil }
  # ints each |a, (b, c)|
  def f405 = ([1, 2, 3]).each { |a, (b, c)| s405_a(a); s405_c(c); nil }
  # ints map |a|
  def f406 = ([1, 2, 3]).map { |a| s406_a(a); nil }
  # ints map |a, b|
  def f407 = ([1, 2, 3]).map { |a, b| s407_a(a); s407_b(b); nil }
  # ints map |a, |
  def f408 = ([1, 2, 3]).map { |a, | s408_a(a); nil }
  # ints map |a, *r|
  def f409 = ([1, 2, 3]).map { |a, *r| s409_a(a); nil }
  # ints map |(a, b)|
  def f410 = ([1, 2, 3]).map { |(a, b)| s410_a(a); s410_b(b); nil }
  # ints map |(a, b), c|
  def f411 = ([1, 2, 3]).map { |(a, b), c| s411_a(a); s411_c(c); nil }
  # ints map |a, (b, c)|
  def f412 = ([1, 2, 3]).map { |a, (b, c)| s412_a(a); s412_c(c); nil }
  # ints select |a|
  def f413 = ([1, 2, 3]).select { |a| s413_a(a); true }
  # ints select |a, b|
  def f414 = ([1, 2, 3]).select { |a, b| s414_a(a); s414_b(b); true }
  # ints select |a, |
  def f415 = ([1, 2, 3]).select { |a, | s415_a(a); true }
  # ints select |a, *r|
  def f416 = ([1, 2, 3]).select { |a, *r| s416_a(a); true }
  # ints select |(a, b)|
  def f417 = ([1, 2, 3]).select { |(a, b)| s417_a(a); s417_b(b); true }
  # ints select |(a, b), c|
  def f418 = ([1, 2, 3]).select { |(a, b), c| s418_a(a); s418_c(c); true }
  # ints select |a, (b, c)|
  def f419 = ([1, 2, 3]).select { |a, (b, c)| s419_a(a); s419_c(c); true }
  # ints reject |a|
  def f420 = ([1, 2, 3]).reject { |a| s420_a(a); false }
  # ints reject |a, b|
  def f421 = ([1, 2, 3]).reject { |a, b| s421_a(a); s421_b(b); false }
  # ints reject |a, |
  def f422 = ([1, 2, 3]).reject { |a, | s422_a(a); false }
  # ints reject |a, *r|
  def f423 = ([1, 2, 3]).reject { |a, *r| s423_a(a); false }
  # ints reject |(a, b)|
  def f424 = ([1, 2, 3]).reject { |(a, b)| s424_a(a); s424_b(b); false }
  # ints reject |(a, b), c|
  def f425 = ([1, 2, 3]).reject { |(a, b), c| s425_a(a); s425_c(c); false }
  # ints reject |a, (b, c)|
  def f426 = ([1, 2, 3]).reject { |a, (b, c)| s426_a(a); s426_c(c); false }
  # ints each_with_index |a|
  def f427 = ([1, 2, 3]).each_with_index { |a| s427_a(a); nil }
  # ints each_with_index |a, b|
  def f428 = ([1, 2, 3]).each_with_index { |a, b| s428_a(a); s428_b(b); nil }
  # ints each_with_index |a, |
  def f429 = ([1, 2, 3]).each_with_index { |a, | s429_a(a); nil }
  # ints each_with_index |a, *r|
  def f430 = ([1, 2, 3]).each_with_index { |a, *r| s430_a(a); nil }
  # ints each_with_index |(a, b)|
  def f431 = ([1, 2, 3]).each_with_index { |(a, b)| s431_a(a); s431_b(b); nil }
  # ints each_with_index |(a, b), c|
  def f432 = ([1, 2, 3]).each_with_index { |(a, b), c| s432_a(a); s432_c(c); nil }
  # ints each_with_index |a, (b, c)|
  def f433 = ([1, 2, 3]).each_with_index { |a, (b, c)| s433_a(a); s433_c(c); nil }
  # ints sort_by |a|
  def f434 = ([1, 2, 3]).sort_by { |a| s434_a(a); 0 }
  # ints sort_by |a, b|
  def f435 = ([1, 2, 3]).sort_by { |a, b| s435_a(a); s435_b(b); 0 }
  # ints sort_by |a, |
  def f436 = ([1, 2, 3]).sort_by { |a, | s436_a(a); 0 }
  # ints sort_by |a, *r|
  def f437 = ([1, 2, 3]).sort_by { |a, *r| s437_a(a); 0 }
  # ints sort_by |(a, b)|
  def f438 = ([1, 2, 3]).sort_by { |(a, b)| s438_a(a); s438_b(b); 0 }
  # ints sort_by |(a, b), c|
  def f439 = ([1, 2, 3]).sort_by { |(a, b), c| s439_a(a); s439_c(c); 0 }
  # ints sort_by |a, (b, c)|
  def f440 = ([1, 2, 3]).sort_by { |a, (b, c)| s440_a(a); s440_c(c); 0 }
  # ints min_by |a|
  def f441 = ([1, 2, 3]).min_by { |a| s441_a(a); 0 }
  # ints min_by |a, b|
  def f442 = ([1, 2, 3]).min_by { |a, b| s442_a(a); s442_b(b); 0 }
  # ints min_by |a, |
  def f443 = ([1, 2, 3]).min_by { |a, | s443_a(a); 0 }
  # ints min_by |a, *r|
  def f444 = ([1, 2, 3]).min_by { |a, *r| s444_a(a); 0 }
  # ints min_by |(a, b)|
  def f445 = ([1, 2, 3]).min_by { |(a, b)| s445_a(a); s445_b(b); 0 }
  # ints min_by |(a, b), c|
  def f446 = ([1, 2, 3]).min_by { |(a, b), c| s446_a(a); s446_c(c); 0 }
  # ints min_by |a, (b, c)|
  def f447 = ([1, 2, 3]).min_by { |a, (b, c)| s447_a(a); s447_c(c); 0 }
  # ints group_by |a|
  def f448 = ([1, 2, 3]).group_by { |a| s448_a(a); 0 }
  # ints group_by |a, b|
  def f449 = ([1, 2, 3]).group_by { |a, b| s449_a(a); s449_b(b); 0 }
  # ints group_by |a, |
  def f450 = ([1, 2, 3]).group_by { |a, | s450_a(a); 0 }
  # ints group_by |a, *r|
  def f451 = ([1, 2, 3]).group_by { |a, *r| s451_a(a); 0 }
  # ints group_by |(a, b)|
  def f452 = ([1, 2, 3]).group_by { |(a, b)| s452_a(a); s452_b(b); 0 }
  # ints group_by |(a, b), c|
  def f453 = ([1, 2, 3]).group_by { |(a, b), c| s453_a(a); s453_c(c); 0 }
  # ints group_by |a, (b, c)|
  def f454 = ([1, 2, 3]).group_by { |a, (b, c)| s454_a(a); s454_c(c); 0 }
  # ints sum |a|
  def f455 = ([1, 2, 3]).sum { |a| s455_a(a); 0 }
  # ints sum |a, b|
  def f456 = ([1, 2, 3]).sum { |a, b| s456_a(a); s456_b(b); 0 }
  # ints sum |a, |
  def f457 = ([1, 2, 3]).sum { |a, | s457_a(a); 0 }
  # ints sum |a, *r|
  def f458 = ([1, 2, 3]).sum { |a, *r| s458_a(a); 0 }
  # ints sum |(a, b)|
  def f459 = ([1, 2, 3]).sum { |(a, b)| s459_a(a); s459_b(b); 0 }
  # ints sum |(a, b), c|
  def f460 = ([1, 2, 3]).sum { |(a, b), c| s460_a(a); s460_c(c); 0 }
  # ints sum |a, (b, c)|
  def f461 = ([1, 2, 3]).sum { |a, (b, c)| s461_a(a); s461_c(c); 0 }
  # ints filter_map |a|
  def f462 = ([1, 2, 3]).filter_map { |a| s462_a(a); nil }
  # ints filter_map |a, b|
  def f463 = ([1, 2, 3]).filter_map { |a, b| s463_a(a); s463_b(b); nil }
  # ints filter_map |a, |
  def f464 = ([1, 2, 3]).filter_map { |a, | s464_a(a); nil }
  # ints filter_map |a, *r|
  def f465 = ([1, 2, 3]).filter_map { |a, *r| s465_a(a); nil }
  # ints filter_map |(a, b)|
  def f466 = ([1, 2, 3]).filter_map { |(a, b)| s466_a(a); s466_b(b); nil }
  # ints filter_map |(a, b), c|
  def f467 = ([1, 2, 3]).filter_map { |(a, b), c| s467_a(a); s467_c(c); nil }
  # ints filter_map |a, (b, c)|
  def f468 = ([1, 2, 3]).filter_map { |a, (b, c)| s468_a(a); s468_c(c); nil }
  # ints flat_map |a|
  def f469 = ([1, 2, 3]).flat_map { |a| s469_a(a); [] }
  # ints flat_map |a, b|
  def f470 = ([1, 2, 3]).flat_map { |a, b| s470_a(a); s470_b(b); [] }
  # ints flat_map |a, |
  def f471 = ([1, 2, 3]).flat_map { |a, | s471_a(a); [] }
  # ints flat_map |a, *r|
  def f472 = ([1, 2, 3]).flat_map { |a, *r| s472_a(a); [] }
  # ints flat_map |(a, b)|
  def f473 = ([1, 2, 3]).flat_map { |(a, b)| s473_a(a); s473_b(b); [] }
  # ints flat_map |(a, b), c|
  def f474 = ([1, 2, 3]).flat_map { |(a, b), c| s474_a(a); s474_c(c); [] }
  # ints flat_map |a, (b, c)|
  def f475 = ([1, 2, 3]).flat_map { |a, (b, c)| s475_a(a); s475_c(c); [] }
  # ints count |a|
  def f476 = ([1, 2, 3]).count { |a| s476_a(a); true }
  # ints count |a, b|
  def f477 = ([1, 2, 3]).count { |a, b| s477_a(a); s477_b(b); true }
  # ints count |a, |
  def f478 = ([1, 2, 3]).count { |a, | s478_a(a); true }
  # ints count |a, *r|
  def f479 = ([1, 2, 3]).count { |a, *r| s479_a(a); true }
  # ints count |(a, b)|
  def f480 = ([1, 2, 3]).count { |(a, b)| s480_a(a); s480_b(b); true }
  # ints count |(a, b), c|
  def f481 = ([1, 2, 3]).count { |(a, b), c| s481_a(a); s481_c(c); true }
  # ints count |a, (b, c)|
  def f482 = ([1, 2, 3]).count { |a, (b, c)| s482_a(a); s482_c(c); true }
  # ints find |a|
  def f483 = ([1, 2, 3]).find { |a| s483_a(a); false }
  # ints find |a, b|
  def f484 = ([1, 2, 3]).find { |a, b| s484_a(a); s484_b(b); false }
  # ints find |a, |
  def f485 = ([1, 2, 3]).find { |a, | s485_a(a); false }
  # ints find |a, *r|
  def f486 = ([1, 2, 3]).find { |a, *r| s486_a(a); false }
  # ints find |(a, b)|
  def f487 = ([1, 2, 3]).find { |(a, b)| s487_a(a); s487_b(b); false }
  # ints find |(a, b), c|
  def f488 = ([1, 2, 3]).find { |(a, b), c| s488_a(a); s488_c(c); false }
  # ints find |a, (b, c)|
  def f489 = ([1, 2, 3]).find { |a, (b, c)| s489_a(a); s489_c(c); false }
  # ints any? |a|
  def f490 = ([1, 2, 3]).any? { |a| s490_a(a); false }
  # ints any? |a, b|
  def f491 = ([1, 2, 3]).any? { |a, b| s491_a(a); s491_b(b); false }
  # ints any? |a, |
  def f492 = ([1, 2, 3]).any? { |a, | s492_a(a); false }
  # ints any? |a, *r|
  def f493 = ([1, 2, 3]).any? { |a, *r| s493_a(a); false }
  # ints any? |(a, b)|
  def f494 = ([1, 2, 3]).any? { |(a, b)| s494_a(a); s494_b(b); false }
  # ints any? |(a, b), c|
  def f495 = ([1, 2, 3]).any? { |(a, b), c| s495_a(a); s495_c(c); false }
  # ints any? |a, (b, c)|
  def f496 = ([1, 2, 3]).any? { |a, (b, c)| s496_a(a); s496_c(c); false }
  # ints partition |a|
  def f497 = ([1, 2, 3]).partition { |a| s497_a(a); true }
  # ints partition |a, b|
  def f498 = ([1, 2, 3]).partition { |a, b| s498_a(a); s498_b(b); true }
  # ints partition |a, |
  def f499 = ([1, 2, 3]).partition { |a, | s499_a(a); true }
  # ints partition |a, *r|
  def f500 = ([1, 2, 3]).partition { |a, *r| s500_a(a); true }
  # ints partition |(a, b)|
  def f501 = ([1, 2, 3]).partition { |(a, b)| s501_a(a); s501_b(b); true }
  # ints partition |(a, b), c|
  def f502 = ([1, 2, 3]).partition { |(a, b), c| s502_a(a); s502_c(c); true }
  # ints partition |a, (b, c)|
  def f503 = ([1, 2, 3]).partition { |a, (b, c)| s503_a(a); s503_c(c); true }
  # ints each_slice |a|
  def f504 = ([1, 2, 3]).each_slice(2) { |a| s504_a(a); nil }
  # ints each_slice |a, b|
  def f505 = ([1, 2, 3]).each_slice(2) { |a, b| s505_a(a); s505_b(b); nil }
  # ints each_slice |a, |
  def f506 = ([1, 2, 3]).each_slice(2) { |a, | s506_a(a); nil }
  # ints each_slice |a, *r|
  def f507 = ([1, 2, 3]).each_slice(2) { |a, *r| s507_a(a); nil }
  # ints each_slice |(a, b)|
  def f508 = ([1, 2, 3]).each_slice(2) { |(a, b)| s508_a(a); s508_b(b); nil }
  # ints each_slice |(a, b), c|
  def f509 = ([1, 2, 3]).each_slice(2) { |(a, b), c| s509_a(a); s509_c(c); nil }
  # ints each_slice |a, (b, c)|
  def f510 = ([1, 2, 3]).each_slice(2) { |a, (b, c)| s510_a(a); s510_c(c); nil }
  # ints each_cons |a|
  def f511 = ([1, 2, 3]).each_cons(2) { |a| s511_a(a); nil }
  # ints each_cons |a, b|
  def f512 = ([1, 2, 3]).each_cons(2) { |a, b| s512_a(a); s512_b(b); nil }
  # ints each_cons |a, |
  def f513 = ([1, 2, 3]).each_cons(2) { |a, | s513_a(a); nil }
  # ints each_cons |a, *r|
  def f514 = ([1, 2, 3]).each_cons(2) { |a, *r| s514_a(a); nil }
  # ints each_cons |(a, b)|
  def f515 = ([1, 2, 3]).each_cons(2) { |(a, b)| s515_a(a); s515_b(b); nil }
  # ints each_cons |(a, b), c|
  def f516 = ([1, 2, 3]).each_cons(2) { |(a, b), c| s516_a(a); s516_c(c); nil }
  # ints each_cons |a, (b, c)|
  def f517 = ([1, 2, 3]).each_cons(2) { |a, (b, c)| s517_a(a); s517_c(c); nil }
  # ints each_with_object |a|
  def f518 = ([1, 2, 3]).each_with_object([]) { |a| s518_a(a); nil }
  # ints each_with_object |a, b|
  def f519 = ([1, 2, 3]).each_with_object([]) { |a, b| s519_a(a); s519_b(b); nil }
  # ints each_with_object |a, |
  def f520 = ([1, 2, 3]).each_with_object([]) { |a, | s520_a(a); nil }
  # ints each_with_object |a, *r|
  def f521 = ([1, 2, 3]).each_with_object([]) { |a, *r| s521_a(a); nil }
  # ints each_with_object |(a, b)|
  def f522 = ([1, 2, 3]).each_with_object([]) { |(a, b)| s522_a(a); s522_b(b); nil }
  # ints each_with_object |(a, b), c|
  def f523 = ([1, 2, 3]).each_with_object([]) { |(a, b), c| s523_a(a); s523_c(c); nil }
  # ints each_with_object |a, (b, c)|
  def f524 = ([1, 2, 3]).each_with_object([]) { |a, (b, c)| s524_a(a); s524_c(c); nil }
  # ints inject |a|
  def f525 = ([1, 2, 3]).inject(0) { |a| s525_a(a); 0 }
  # ints inject |a, b|
  def f526 = ([1, 2, 3]).inject(0) { |a, b| s526_a(a); s526_b(b); 0 }
  # ints inject |a, |
  def f527 = ([1, 2, 3]).inject(0) { |a, | s527_a(a); 0 }
  # ints inject |a, *r|
  def f528 = ([1, 2, 3]).inject(0) { |a, *r| s528_a(a); 0 }
  # ints inject |(a, b)|
  def f529 = ([1, 2, 3]).inject(0) { |(a, b)| s529_a(a); s529_b(b); 0 }
  # ints inject |(a, b), c|
  def f530 = ([1, 2, 3]).inject(0) { |(a, b), c| s530_a(a); s530_c(c); 0 }
  # ints inject |a, (b, c)|
  def f531 = ([1, 2, 3]).inject(0) { |a, (b, c)| s531_a(a); s531_c(c); 0 }

  def s0_a(x) = x
  def s1_a(x) = x
  def s1_b(x) = x
  def s2_a(x) = x
  def s3_a(x) = x
  def s4_a(x) = x
  def s4_b(x) = x
  def s5_a(x) = x
  def s5_c(x) = x
  def s6_a(x) = x
  def s6_c(x) = x
  def s7_a(x) = x
  def s8_a(x) = x
  def s8_b(x) = x
  def s9_a(x) = x
  def s10_a(x) = x
  def s11_a(x) = x
  def s11_b(x) = x
  def s12_a(x) = x
  def s12_c(x) = x
  def s13_a(x) = x
  def s13_c(x) = x
  def s14_a(x) = x
  def s15_a(x) = x
  def s15_b(x) = x
  def s16_a(x) = x
  def s17_a(x) = x
  def s18_a(x) = x
  def s18_b(x) = x
  def s19_a(x) = x
  def s19_c(x) = x
  def s20_a(x) = x
  def s20_c(x) = x
  def s21_a(x) = x
  def s22_a(x) = x
  def s22_b(x) = x
  def s23_a(x) = x
  def s24_a(x) = x
  def s25_a(x) = x
  def s25_b(x) = x
  def s26_a(x) = x
  def s26_c(x) = x
  def s27_a(x) = x
  def s27_c(x) = x
  def s28_a(x) = x
  def s29_a(x) = x
  def s29_b(x) = x
  def s30_a(x) = x
  def s31_a(x) = x
  def s32_a(x) = x
  def s32_b(x) = x
  def s33_a(x) = x
  def s33_c(x) = x
  def s34_a(x) = x
  def s34_c(x) = x
  def s35_a(x) = x
  def s36_a(x) = x
  def s36_b(x) = x
  def s37_a(x) = x
  def s38_a(x) = x
  def s39_a(x) = x
  def s39_b(x) = x
  def s40_a(x) = x
  def s40_c(x) = x
  def s41_a(x) = x
  def s41_c(x) = x
  def s42_a(x) = x
  def s43_a(x) = x
  def s43_b(x) = x
  def s44_a(x) = x
  def s45_a(x) = x
  def s46_a(x) = x
  def s46_b(x) = x
  def s47_a(x) = x
  def s47_c(x) = x
  def s48_a(x) = x
  def s48_c(x) = x
  def s49_a(x) = x
  def s50_a(x) = x
  def s50_b(x) = x
  def s51_a(x) = x
  def s52_a(x) = x
  def s53_a(x) = x
  def s53_b(x) = x
  def s54_a(x) = x
  def s54_c(x) = x
  def s55_a(x) = x
  def s55_c(x) = x
  def s56_a(x) = x
  def s57_a(x) = x
  def s57_b(x) = x
  def s58_a(x) = x
  def s59_a(x) = x
  def s60_a(x) = x
  def s60_b(x) = x
  def s61_a(x) = x
  def s61_c(x) = x
  def s62_a(x) = x
  def s62_c(x) = x
  def s63_a(x) = x
  def s64_a(x) = x
  def s64_b(x) = x
  def s65_a(x) = x
  def s66_a(x) = x
  def s67_a(x) = x
  def s67_b(x) = x
  def s68_a(x) = x
  def s68_c(x) = x
  def s69_a(x) = x
  def s69_c(x) = x
  def s70_a(x) = x
  def s71_a(x) = x
  def s71_b(x) = x
  def s72_a(x) = x
  def s73_a(x) = x
  def s74_a(x) = x
  def s74_b(x) = x
  def s75_a(x) = x
  def s75_c(x) = x
  def s76_a(x) = x
  def s76_c(x) = x
  def s77_a(x) = x
  def s78_a(x) = x
  def s78_b(x) = x
  def s79_a(x) = x
  def s80_a(x) = x
  def s81_a(x) = x
  def s81_b(x) = x
  def s82_a(x) = x
  def s82_c(x) = x
  def s83_a(x) = x
  def s83_c(x) = x
  def s84_a(x) = x
  def s85_a(x) = x
  def s85_b(x) = x
  def s86_a(x) = x
  def s87_a(x) = x
  def s88_a(x) = x
  def s88_b(x) = x
  def s89_a(x) = x
  def s89_c(x) = x
  def s90_a(x) = x
  def s90_c(x) = x
  def s91_a(x) = x
  def s92_a(x) = x
  def s92_b(x) = x
  def s93_a(x) = x
  def s94_a(x) = x
  def s95_a(x) = x
  def s95_b(x) = x
  def s96_a(x) = x
  def s96_c(x) = x
  def s97_a(x) = x
  def s97_c(x) = x
  def s98_a(x) = x
  def s99_a(x) = x
  def s99_b(x) = x
  def s100_a(x) = x
  def s101_a(x) = x
  def s102_a(x) = x
  def s102_b(x) = x
  def s103_a(x) = x
  def s103_c(x) = x
  def s104_a(x) = x
  def s104_c(x) = x
  def s105_a(x) = x
  def s106_a(x) = x
  def s106_b(x) = x
  def s107_a(x) = x
  def s108_a(x) = x
  def s109_a(x) = x
  def s109_b(x) = x
  def s110_a(x) = x
  def s110_c(x) = x
  def s111_a(x) = x
  def s111_c(x) = x
  def s112_a(x) = x
  def s113_a(x) = x
  def s113_b(x) = x
  def s114_a(x) = x
  def s115_a(x) = x
  def s116_a(x) = x
  def s116_b(x) = x
  def s117_a(x) = x
  def s117_c(x) = x
  def s118_a(x) = x
  def s118_c(x) = x
  def s119_a(x) = x
  def s120_a(x) = x
  def s120_b(x) = x
  def s121_a(x) = x
  def s122_a(x) = x
  def s123_a(x) = x
  def s123_b(x) = x
  def s124_a(x) = x
  def s124_c(x) = x
  def s125_a(x) = x
  def s125_c(x) = x
  def s126_a(x) = x
  def s127_a(x) = x
  def s127_b(x) = x
  def s128_a(x) = x
  def s129_a(x) = x
  def s130_a(x) = x
  def s130_b(x) = x
  def s131_a(x) = x
  def s131_c(x) = x
  def s132_a(x) = x
  def s132_c(x) = x
  def s133_a(x) = x
  def s134_a(x) = x
  def s134_b(x) = x
  def s135_a(x) = x
  def s136_a(x) = x
  def s137_a(x) = x
  def s137_b(x) = x
  def s138_a(x) = x
  def s138_c(x) = x
  def s139_a(x) = x
  def s139_c(x) = x
  def s140_a(x) = x
  def s141_a(x) = x
  def s141_b(x) = x
  def s142_a(x) = x
  def s143_a(x) = x
  def s144_a(x) = x
  def s144_b(x) = x
  def s145_a(x) = x
  def s145_c(x) = x
  def s146_a(x) = x
  def s146_c(x) = x
  def s147_a(x) = x
  def s148_a(x) = x
  def s148_b(x) = x
  def s149_a(x) = x
  def s150_a(x) = x
  def s151_a(x) = x
  def s151_b(x) = x
  def s152_a(x) = x
  def s152_c(x) = x
  def s153_a(x) = x
  def s153_c(x) = x
  def s154_a(x) = x
  def s155_a(x) = x
  def s155_b(x) = x
  def s156_a(x) = x
  def s157_a(x) = x
  def s158_a(x) = x
  def s158_b(x) = x
  def s159_a(x) = x
  def s159_c(x) = x
  def s160_a(x) = x
  def s160_c(x) = x
  def s161_a(x) = x
  def s162_a(x) = x
  def s162_b(x) = x
  def s163_a(x) = x
  def s164_a(x) = x
  def s165_a(x) = x
  def s165_b(x) = x
  def s166_a(x) = x
  def s166_c(x) = x
  def s167_a(x) = x
  def s167_c(x) = x
  def s168_a(x) = x
  def s169_a(x) = x
  def s169_b(x) = x
  def s170_a(x) = x
  def s171_a(x) = x
  def s172_a(x) = x
  def s172_b(x) = x
  def s173_a(x) = x
  def s173_c(x) = x
  def s174_a(x) = x
  def s174_c(x) = x
  def s175_a(x) = x
  def s176_a(x) = x
  def s176_b(x) = x
  def s177_a(x) = x
  def s178_a(x) = x
  def s179_a(x) = x
  def s179_b(x) = x
  def s180_a(x) = x
  def s180_c(x) = x
  def s181_a(x) = x
  def s181_c(x) = x
  def s182_a(x) = x
  def s183_a(x) = x
  def s183_b(x) = x
  def s184_a(x) = x
  def s185_a(x) = x
  def s186_a(x) = x
  def s186_b(x) = x
  def s187_a(x) = x
  def s187_c(x) = x
  def s188_a(x) = x
  def s188_c(x) = x
  def s189_a(x) = x
  def s190_a(x) = x
  def s190_b(x) = x
  def s191_a(x) = x
  def s192_a(x) = x
  def s193_a(x) = x
  def s193_b(x) = x
  def s194_a(x) = x
  def s194_c(x) = x
  def s195_a(x) = x
  def s195_c(x) = x
  def s196_a(x) = x
  def s197_a(x) = x
  def s197_b(x) = x
  def s198_a(x) = x
  def s199_a(x) = x
  def s200_a(x) = x
  def s200_b(x) = x
  def s201_a(x) = x
  def s201_c(x) = x
  def s202_a(x) = x
  def s202_c(x) = x
  def s203_a(x) = x
  def s204_a(x) = x
  def s204_b(x) = x
  def s205_a(x) = x
  def s206_a(x) = x
  def s207_a(x) = x
  def s207_b(x) = x
  def s208_a(x) = x
  def s208_c(x) = x
  def s209_a(x) = x
  def s209_c(x) = x
  def s210_a(x) = x
  def s211_a(x) = x
  def s211_b(x) = x
  def s212_a(x) = x
  def s213_a(x) = x
  def s214_a(x) = x
  def s214_b(x) = x
  def s215_a(x) = x
  def s215_c(x) = x
  def s216_a(x) = x
  def s216_c(x) = x
  def s217_a(x) = x
  def s218_a(x) = x
  def s218_b(x) = x
  def s219_a(x) = x
  def s220_a(x) = x
  def s221_a(x) = x
  def s221_b(x) = x
  def s222_a(x) = x
  def s222_c(x) = x
  def s223_a(x) = x
  def s223_c(x) = x
  def s224_a(x) = x
  def s225_a(x) = x
  def s225_b(x) = x
  def s226_a(x) = x
  def s227_a(x) = x
  def s228_a(x) = x
  def s228_b(x) = x
  def s229_a(x) = x
  def s229_c(x) = x
  def s230_a(x) = x
  def s230_c(x) = x
  def s231_a(x) = x
  def s232_a(x) = x
  def s232_b(x) = x
  def s233_a(x) = x
  def s234_a(x) = x
  def s235_a(x) = x
  def s235_b(x) = x
  def s236_a(x) = x
  def s236_c(x) = x
  def s237_a(x) = x
  def s237_c(x) = x
  def s238_a(x) = x
  def s239_a(x) = x
  def s239_b(x) = x
  def s240_a(x) = x
  def s241_a(x) = x
  def s242_a(x) = x
  def s242_b(x) = x
  def s243_a(x) = x
  def s243_c(x) = x
  def s244_a(x) = x
  def s244_c(x) = x
  def s245_a(x) = x
  def s246_a(x) = x
  def s246_b(x) = x
  def s247_a(x) = x
  def s248_a(x) = x
  def s249_a(x) = x
  def s249_b(x) = x
  def s250_a(x) = x
  def s250_c(x) = x
  def s251_a(x) = x
  def s251_c(x) = x
  def s252_a(x) = x
  def s253_a(x) = x
  def s253_b(x) = x
  def s254_a(x) = x
  def s255_a(x) = x
  def s256_a(x) = x
  def s256_b(x) = x
  def s257_a(x) = x
  def s257_c(x) = x
  def s258_a(x) = x
  def s258_c(x) = x
  def s259_a(x) = x
  def s260_a(x) = x
  def s260_b(x) = x
  def s261_a(x) = x
  def s262_a(x) = x
  def s263_a(x) = x
  def s263_b(x) = x
  def s264_a(x) = x
  def s264_c(x) = x
  def s265_a(x) = x
  def s265_c(x) = x
  def s266_a(x) = x
  def s267_a(x) = x
  def s267_b(x) = x
  def s268_a(x) = x
  def s269_a(x) = x
  def s270_a(x) = x
  def s270_b(x) = x
  def s271_a(x) = x
  def s271_c(x) = x
  def s272_a(x) = x
  def s272_c(x) = x
  def s273_a(x) = x
  def s274_a(x) = x
  def s274_b(x) = x
  def s275_a(x) = x
  def s276_a(x) = x
  def s277_a(x) = x
  def s277_b(x) = x
  def s278_a(x) = x
  def s278_c(x) = x
  def s279_a(x) = x
  def s279_c(x) = x
  def s280_a(x) = x
  def s281_a(x) = x
  def s281_b(x) = x
  def s282_a(x) = x
  def s283_a(x) = x
  def s284_a(x) = x
  def s284_b(x) = x
  def s285_a(x) = x
  def s285_c(x) = x
  def s286_a(x) = x
  def s286_c(x) = x
  def s287_a(x) = x
  def s288_a(x) = x
  def s288_b(x) = x
  def s289_a(x) = x
  def s290_a(x) = x
  def s291_a(x) = x
  def s291_b(x) = x
  def s292_a(x) = x
  def s292_c(x) = x
  def s293_a(x) = x
  def s293_c(x) = x
  def s294_a(x) = x
  def s295_a(x) = x
  def s295_b(x) = x
  def s296_a(x) = x
  def s297_a(x) = x
  def s298_a(x) = x
  def s298_b(x) = x
  def s299_a(x) = x
  def s299_c(x) = x
  def s300_a(x) = x
  def s300_c(x) = x
  def s301_a(x) = x
  def s302_a(x) = x
  def s302_b(x) = x
  def s303_a(x) = x
  def s304_a(x) = x
  def s305_a(x) = x
  def s305_b(x) = x
  def s306_a(x) = x
  def s306_c(x) = x
  def s307_a(x) = x
  def s307_c(x) = x
  def s308_a(x) = x
  def s309_a(x) = x
  def s309_b(x) = x
  def s310_a(x) = x
  def s311_a(x) = x
  def s312_a(x) = x
  def s312_b(x) = x
  def s313_a(x) = x
  def s313_c(x) = x
  def s314_a(x) = x
  def s314_c(x) = x
  def s315_a(x) = x
  def s316_a(x) = x
  def s316_b(x) = x
  def s317_a(x) = x
  def s318_a(x) = x
  def s319_a(x) = x
  def s319_b(x) = x
  def s320_a(x) = x
  def s320_c(x) = x
  def s321_a(x) = x
  def s321_c(x) = x
  def s322_a(x) = x
  def s323_a(x) = x
  def s323_b(x) = x
  def s324_a(x) = x
  def s325_a(x) = x
  def s326_a(x) = x
  def s326_b(x) = x
  def s327_a(x) = x
  def s327_c(x) = x
  def s328_a(x) = x
  def s328_c(x) = x
  def s329_a(x) = x
  def s330_a(x) = x
  def s330_b(x) = x
  def s331_a(x) = x
  def s332_a(x) = x
  def s333_a(x) = x
  def s333_b(x) = x
  def s334_a(x) = x
  def s334_c(x) = x
  def s335_a(x) = x
  def s335_c(x) = x
  def s336_a(x) = x
  def s337_a(x) = x
  def s337_b(x) = x
  def s338_a(x) = x
  def s339_a(x) = x
  def s340_a(x) = x
  def s340_b(x) = x
  def s341_a(x) = x
  def s341_c(x) = x
  def s342_a(x) = x
  def s342_c(x) = x
  def s343_a(x) = x
  def s344_a(x) = x
  def s344_b(x) = x
  def s345_a(x) = x
  def s346_a(x) = x
  def s347_a(x) = x
  def s347_b(x) = x
  def s348_a(x) = x
  def s348_c(x) = x
  def s349_a(x) = x
  def s349_c(x) = x
  def s350_a(x) = x
  def s351_a(x) = x
  def s351_b(x) = x
  def s352_a(x) = x
  def s353_a(x) = x
  def s354_a(x) = x
  def s354_b(x) = x
  def s355_a(x) = x
  def s355_c(x) = x
  def s356_a(x) = x
  def s356_c(x) = x
  def s357_a(x) = x
  def s358_a(x) = x
  def s358_b(x) = x
  def s359_a(x) = x
  def s360_a(x) = x
  def s361_a(x) = x
  def s361_b(x) = x
  def s362_a(x) = x
  def s362_c(x) = x
  def s363_a(x) = x
  def s363_c(x) = x
  def s364_a(x) = x
  def s365_a(x) = x
  def s365_b(x) = x
  def s366_a(x) = x
  def s367_a(x) = x
  def s368_a(x) = x
  def s368_b(x) = x
  def s369_a(x) = x
  def s369_c(x) = x
  def s370_a(x) = x
  def s370_c(x) = x
  def s371_a(x) = x
  def s372_a(x) = x
  def s372_b(x) = x
  def s373_a(x) = x
  def s374_a(x) = x
  def s375_a(x) = x
  def s375_b(x) = x
  def s376_a(x) = x
  def s376_c(x) = x
  def s377_a(x) = x
  def s377_c(x) = x
  def s378_a(x) = x
  def s379_a(x) = x
  def s379_b(x) = x
  def s380_a(x) = x
  def s381_a(x) = x
  def s382_a(x) = x
  def s382_b(x) = x
  def s383_a(x) = x
  def s383_c(x) = x
  def s384_a(x) = x
  def s384_c(x) = x
  def s385_a(x) = x
  def s386_a(x) = x
  def s386_b(x) = x
  def s387_a(x) = x
  def s388_a(x) = x
  def s389_a(x) = x
  def s389_b(x) = x
  def s390_a(x) = x
  def s390_c(x) = x
  def s391_a(x) = x
  def s391_c(x) = x
  def s392_a(x) = x
  def s393_a(x) = x
  def s393_b(x) = x
  def s394_a(x) = x
  def s395_a(x) = x
  def s396_a(x) = x
  def s396_b(x) = x
  def s397_a(x) = x
  def s397_c(x) = x
  def s398_a(x) = x
  def s398_c(x) = x
  def s399_a(x) = x
  def s400_a(x) = x
  def s400_b(x) = x
  def s401_a(x) = x
  def s402_a(x) = x
  def s403_a(x) = x
  def s403_b(x) = x
  def s404_a(x) = x
  def s404_c(x) = x
  def s405_a(x) = x
  def s405_c(x) = x
  def s406_a(x) = x
  def s407_a(x) = x
  def s407_b(x) = x
  def s408_a(x) = x
  def s409_a(x) = x
  def s410_a(x) = x
  def s410_b(x) = x
  def s411_a(x) = x
  def s411_c(x) = x
  def s412_a(x) = x
  def s412_c(x) = x
  def s413_a(x) = x
  def s414_a(x) = x
  def s414_b(x) = x
  def s415_a(x) = x
  def s416_a(x) = x
  def s417_a(x) = x
  def s417_b(x) = x
  def s418_a(x) = x
  def s418_c(x) = x
  def s419_a(x) = x
  def s419_c(x) = x
  def s420_a(x) = x
  def s421_a(x) = x
  def s421_b(x) = x
  def s422_a(x) = x
  def s423_a(x) = x
  def s424_a(x) = x
  def s424_b(x) = x
  def s425_a(x) = x
  def s425_c(x) = x
  def s426_a(x) = x
  def s426_c(x) = x
  def s427_a(x) = x
  def s428_a(x) = x
  def s428_b(x) = x
  def s429_a(x) = x
  def s430_a(x) = x
  def s431_a(x) = x
  def s431_b(x) = x
  def s432_a(x) = x
  def s432_c(x) = x
  def s433_a(x) = x
  def s433_c(x) = x
  def s434_a(x) = x
  def s435_a(x) = x
  def s435_b(x) = x
  def s436_a(x) = x
  def s437_a(x) = x
  def s438_a(x) = x
  def s438_b(x) = x
  def s439_a(x) = x
  def s439_c(x) = x
  def s440_a(x) = x
  def s440_c(x) = x
  def s441_a(x) = x
  def s442_a(x) = x
  def s442_b(x) = x
  def s443_a(x) = x
  def s444_a(x) = x
  def s445_a(x) = x
  def s445_b(x) = x
  def s446_a(x) = x
  def s446_c(x) = x
  def s447_a(x) = x
  def s447_c(x) = x
  def s448_a(x) = x
  def s449_a(x) = x
  def s449_b(x) = x
  def s450_a(x) = x
  def s451_a(x) = x
  def s452_a(x) = x
  def s452_b(x) = x
  def s453_a(x) = x
  def s453_c(x) = x
  def s454_a(x) = x
  def s454_c(x) = x
  def s455_a(x) = x
  def s456_a(x) = x
  def s456_b(x) = x
  def s457_a(x) = x
  def s458_a(x) = x
  def s459_a(x) = x
  def s459_b(x) = x
  def s460_a(x) = x
  def s460_c(x) = x
  def s461_a(x) = x
  def s461_c(x) = x
  def s462_a(x) = x
  def s463_a(x) = x
  def s463_b(x) = x
  def s464_a(x) = x
  def s465_a(x) = x
  def s466_a(x) = x
  def s466_b(x) = x
  def s467_a(x) = x
  def s467_c(x) = x
  def s468_a(x) = x
  def s468_c(x) = x
  def s469_a(x) = x
  def s470_a(x) = x
  def s470_b(x) = x
  def s471_a(x) = x
  def s472_a(x) = x
  def s473_a(x) = x
  def s473_b(x) = x
  def s474_a(x) = x
  def s474_c(x) = x
  def s475_a(x) = x
  def s475_c(x) = x
  def s476_a(x) = x
  def s477_a(x) = x
  def s477_b(x) = x
  def s478_a(x) = x
  def s479_a(x) = x
  def s480_a(x) = x
  def s480_b(x) = x
  def s481_a(x) = x
  def s481_c(x) = x
  def s482_a(x) = x
  def s482_c(x) = x
  def s483_a(x) = x
  def s484_a(x) = x
  def s484_b(x) = x
  def s485_a(x) = x
  def s486_a(x) = x
  def s487_a(x) = x
  def s487_b(x) = x
  def s488_a(x) = x
  def s488_c(x) = x
  def s489_a(x) = x
  def s489_c(x) = x
  def s490_a(x) = x
  def s491_a(x) = x
  def s491_b(x) = x
  def s492_a(x) = x
  def s493_a(x) = x
  def s494_a(x) = x
  def s494_b(x) = x
  def s495_a(x) = x
  def s495_c(x) = x
  def s496_a(x) = x
  def s496_c(x) = x
  def s497_a(x) = x
  def s498_a(x) = x
  def s498_b(x) = x
  def s499_a(x) = x
  def s500_a(x) = x
  def s501_a(x) = x
  def s501_b(x) = x
  def s502_a(x) = x
  def s502_c(x) = x
  def s503_a(x) = x
  def s503_c(x) = x
  def s504_a(x) = x
  def s505_a(x) = x
  def s505_b(x) = x
  def s506_a(x) = x
  def s507_a(x) = x
  def s508_a(x) = x
  def s508_b(x) = x
  def s509_a(x) = x
  def s509_c(x) = x
  def s510_a(x) = x
  def s510_c(x) = x
  def s511_a(x) = x
  def s512_a(x) = x
  def s512_b(x) = x
  def s513_a(x) = x
  def s514_a(x) = x
  def s515_a(x) = x
  def s515_b(x) = x
  def s516_a(x) = x
  def s516_c(x) = x
  def s517_a(x) = x
  def s517_c(x) = x
  def s518_a(x) = x
  def s519_a(x) = x
  def s519_b(x) = x
  def s520_a(x) = x
  def s521_a(x) = x
  def s522_a(x) = x
  def s522_b(x) = x
  def s523_a(x) = x
  def s523_c(x) = x
  def s524_a(x) = x
  def s524_c(x) = x
  def s525_a(x) = x
  def s526_a(x) = x
  def s526_b(x) = x
  def s527_a(x) = x
  def s528_a(x) = x
  def s529_a(x) = x
  def s529_b(x) = x
  def s530_a(x) = x
  def s530_c(x) = x
  def s531_a(x) = x
  def s531_c(x) = x
end
