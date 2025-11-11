import 'dart:convert';
import 'package:http/http.dart' as http;
import '../utils/config.dart';

class ApiService {
  final String baseUrl = Config.apiUrl;

  Future<List<dynamic>> getProdutos() async {
    final response = await http.get(Uri.parse('$baseUrl/produtos/'));
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Erro ao carregar produtos');
    }
  }

  Future<List<dynamic>> getVendas() async {
    final response = await http.get(Uri.parse('$baseUrl/vendas/'));
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Erro ao carregar vendas');
    }
  }
}
