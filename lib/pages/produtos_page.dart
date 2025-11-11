import 'package:flutter/material.dart';
import '../api/api_service.dart';

class ProdutosPage extends StatefulWidget {
  const ProdutosPage({super.key});

  @override
  State<ProdutosPage> createState() => _ProdutosPageState();
}

class _ProdutosPageState extends State<ProdutosPage> {
  final ApiService api = ApiService();
  List produtos = [];
  bool carregando = true;

  @override
  void initState() {
    super.initState();
    carregarProdutos();
  }

  void carregarProdutos() async {
    final dados = await api.getProdutos();
    setState(() {
      produtos = dados;
      carregando = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Produtos')),
      body: carregando
          ? const Center(child: CircularProgressIndicator())
          : ListView.builder(
              itemCount: produtos.length,
              itemBuilder: (context, index) {
                final p = produtos[index];
                return Card(
                  margin: const EdgeInsets.all(8),
                  child: ListTile(
                    title: Text(p['nome']),
                    subtitle: Text("Categoria: ${p['categoria'] ?? '-'}"),
                    trailing: Text("R\$ ${p['preco_venda'] ?? 0}"),
                  ),
                );
              },
            ),
    );
  }
}
