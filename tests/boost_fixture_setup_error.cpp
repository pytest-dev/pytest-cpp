#include <stdexcept>
#define BOOST_TEST_MODULE MyTest
#include <boost/test/included/unit_test.hpp>

struct InitTests {
    InitTests() {
        fprintf(stdout, "something on the stdout\n");
        fflush(stdout);
        fprintf(stderr, "something on the stderr\n");
        fflush(stderr);
        throw std::runtime_error("This is a global fixture init failure");
    }
};
BOOST_GLOBAL_FIXTURE(InitTests);


BOOST_AUTO_TEST_CASE( test_dummy )
{
    return;
}
