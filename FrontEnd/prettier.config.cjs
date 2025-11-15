module.exports = {
  semi: true,
  singleQuote: false,
  trailingComma: "es5",
  printWidth: 100,

  plugins: ["@trivago/prettier-plugin-sort-imports"],

  importOrder: ["^react$", "<THIRD_PARTY_MODULES>", "^@/components/(.*)$", "^[./]"],
};
