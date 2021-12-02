#include <stdexcept>
#include "gtest/gtest.h"

namespace {

// The fixture for testing class Foo.
class FooTest : public ::testing::Test {
};

// Tests that the Foo::Bar() method does Abc.
TEST_F(FooTest, test_success) {
  EXPECT_EQ(2 * 3, 6);
  printf("Just saying hi from gtest\n");
}

// Tests that the Foo::Bar() method does Abc.
TEST_F(FooTest, test_failure) {
  printf("Just saying hi from gtest\n");
  EXPECT_EQ(2 * 3, 5);
  EXPECT_EQ(2 * 6, 15);
}

// Tests that the Foo::Bar() method does Abc.
TEST_F(FooTest, test_error) {
  throw std::runtime_error("unexpected exception");
}

// Tests that the Foo::Bar() method does Abc.
TEST_F(FooTest, DISABLED_test_disabled) {
  EXPECT_EQ(2 * 6, 10);
}

// Tests that the Foo::Bar() method does Abc.
TEST_F(FooTest, test_skipped) {
  GTEST_SKIP() << "This is a skipped message";
  EXPECT_EQ(true, false);
}

// Tests that the Foo::Bar() method does Abc.
TEST_F(FooTest, test_skipped_no_msg) {
  GTEST_SKIP();
  EXPECT_EQ(true, false);
}

}  // namespace

int main(int argc, char **argv) {
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
