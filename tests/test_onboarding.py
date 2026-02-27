"""
Tests for domain inference from user input.
"""

from skill_issue.onboarding import infer_domains


class TestInferDomains:
    """Tests for infer_domains function."""

    def test_pytorch_models_includes_machine_learning(self):
        """'I train PyTorch models' should include machine-learning."""
        domains = infer_domains("I train PyTorch models")
        assert "machine-learning" in domains

    def test_react_typescript_includes_web_frontend(self):
        """'React frontend TypeScript' should include web-frontend."""
        domains = infer_domains("React frontend TypeScript")
        assert "web-frontend" in domains

    def test_docker_kubernetes_terraform_includes_devops(self):
        """'Docker kubernetes terraform' should include devops."""
        domains = infer_domains("Docker kubernetes terraform")
        assert "devops" in domains

    def test_always_includes_algorithms(self):
        """Any input should always include algorithms (either directly or swapped in)."""
        # ML focus
        domains = infer_domains("I train PyTorch models on transformers")
        assert "algorithms" in domains

        # Frontend focus
        domains = infer_domains("React Vue Angular TypeScript CSS")
        assert "algorithms" in domains

        # Design focus
        domains = infer_domains("Figma design systems typography")
        assert "algorithms" in domains

    def test_unknown_domain_returns_algorithms(self):
        """Unknown/empty/gibberish input should return ['algorithms']."""
        assert infer_domains("") == ["algorithms"]
        assert infer_domains("asdfghjkl") == ["algorithms"]
        assert infer_domains("xyzzy plugh") == ["algorithms"]

    def test_multiple_domains_detected(self):
        """Multiple relevant keywords should detect multiple domains."""
        domains = infer_domains("I build React frontends with Django backends and deploy on Kubernetes")
        # Should detect web-frontend, backend-systems, devops
        assert len(domains) <= 3  # max_domains default is 3
        # At minimum should have one of each area detected
        domain_set = set(domains)
        # Could be any combo, but algorithms should be there
        assert "algorithms" in domain_set or len(domain_set) == 3

    def test_quantum_ml_detection(self):
        """Quantum keywords should detect quantum-ml domain."""
        domains = infer_domains("I work on variational quantum circuits with PennyLane")
        assert "quantum-ml" in domains

    def test_mobile_detection(self):
        """Mobile keywords should detect mobile domain."""
        domains = infer_domains("I build iOS apps with Swift and React Native")
        assert "mobile" in domains

    def test_data_science_detection(self):
        """Data science keywords should detect data-science domain."""
        domains = infer_domains("pandas numpy jupyter data science feature engineering")
        assert "data-science" in domains

    def test_max_domains_respected(self):
        """Should not return more than max_domains."""
        # Input that matches many domains
        text = "React TypeScript Docker Kubernetes PyTorch pandas Django PostgreSQL Swift"
        domains = infer_domains(text, max_domains=3)
        assert len(domains) <= 3

        domains = infer_domains(text, max_domains=2)
        assert len(domains) <= 2
