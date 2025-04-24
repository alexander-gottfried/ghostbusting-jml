import XCTest
import SwiftTreeSitter
import TreeSitterJavaJmlSubset

final class TreeSitterJavaJmlSubsetTests: XCTestCase {
    func testCanLoadGrammar() throws {
        let parser = Parser()
        let language = Language(language: tree_sitter_java_jml_subset())
        XCTAssertNoThrow(try parser.setLanguage(language),
                         "Error loading JavaJmlSubset grammar")
    }
}
