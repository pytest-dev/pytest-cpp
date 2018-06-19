#include "gtest/gtest.h"

namespace {
int argsNumber;
char **args;

TEST(ArgsTest, one_argument) {
  EXPECT_EQ(2, argsNumber);
  EXPECT_STREQ("argument1", args[1]);
}

TEST(ArgsTest, two_arguments) {
  EXPECT_EQ(3, argsNumber);
  EXPECT_STREQ("argument1", args[1]);
  EXPECT_STREQ("argument2", args[2]);
}
}  // namespace

int main(int argc, char **argv) {
  ::testing::InitGoogleTest(&argc, argv);
  argsNumber = argc;
  args = argv;
  return RUN_ALL_TESTS();
}
