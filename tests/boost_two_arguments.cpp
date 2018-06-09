#define BOOST_TEST_MODULE TestTwoArguments
#include <boost/test/included/unit_test.hpp>

BOOST_AUTO_TEST_CASE(two_arguments)
{
    int argc = boost::unit_test::framework::master_test_suite().argc;
    char **argv = boost::unit_test::framework::master_test_suite().argv;

    BOOST_CHECK( argc == 3 );
    BOOST_CHECK_EQUAL(argv[1], "argument1");
    BOOST_CHECK_EQUAL(argv[2], "argument2");
}
